"""
Adaptive Semantic Chunker for GraphRAG Ingestion.
Partitions unstructured corpus into cohesive semantic chunks based on:
1. Markdown structural headers (#, ##, ###)
2. Paragraph boundaries and topic shifts
3. Lexical and topical cohesion scoring
4. Adaptive token sizing with zero redundant tokens
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Set
from ..models.graphrag_ontology import SemanticChunk

# Common stopwords in English and Indonesian to focus cohesion on content tokens
_STOPWORDS: Set[str] = {
    # English
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with",
    "by", "about", "against", "between", "into", "through", "during", "before",
    "after", "above", "below", "from", "up", "down", "of", "off", "over", "under",
    "again", "further", "then", "once", "here", "there", "when", "where", "why",
    "how", "all", "any", "both", "each", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "can", "will", "just", "don", "should", "now", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "this", "that", "these", "those",
    # Indonesian
    "yang", "di", "dan", "dari", "ke", "ini", "itu", "untuk", "pada", "adalah",
    "dengan", "dalam", "bisa", "akan", "juga", "atau", "oleh", "secara", "sebagai",
    "karena", "tersebut", "dapat", "mereka", "kita", "kami", "ia", "dia", "saat",
    "ada", "telah", "lebih", "tidak", "hanya", "serta", "bagi", "sampai", "tentang",
}


class AdaptiveSemanticChunker:
    """
    Adaptive Semantic Chunker based on paragraph boundaries, structural delimiters,
    and topical cohesion scoring.
    """

    def __init__(
        self,
        target_chunk_size: int = 800,
        min_chunk_size: int = 200,
        max_chunk_size: int = 1500,
        cohesion_threshold: float = 0.15,
        preserve_headers: bool = True,
        overlap_sentences: int = 0,
    ):
        self.target_chunk_size = target_chunk_size
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.cohesion_threshold = cohesion_threshold
        self.preserve_headers = preserve_headers
        self.overlap_sentences = overlap_sentences

    @staticmethod
    def extract_content_keywords(text: str) -> Set[str]:
        """Extract alphanumeric keywords of length >= 3, lowercase, excluding stopwords."""
        words = re.findall(r'\b[a-zA-Z0-9_\u4e00-\u9fa5]{3,}\b', text.lower())
        return {w for w in words if w not in _STOPWORDS}

    @classmethod
    def calculate_cohesion(cls, text1: str, text2: str) -> float:
        """
        Calculate lexical-topical cohesion between two consecutive text segments.
        Returns a score in [0.0, 1.0].
        """
        kw1 = cls.extract_content_keywords(text1)
        kw2 = cls.extract_content_keywords(text2)

        if not kw1 or not kw2:
            return 0.0

        intersection = kw1.intersection(kw2)
        union = kw1.union(kw2)
        if not union:
            return 0.0

        return len(intersection) / len(union)

    def segment_into_blocks(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse raw text into structural blocks (markdown headers, paragraphs, lists).
        Tracks character offsets and header levels.
        """
        lines = text.split('\n')
        blocks: List[Dict[str, Any]] = []
        current_paragraph: List[str] = []
        p_start_offset = 0
        current_offset = 0
        current_header = None

        def flush_paragraph(end_offset: int):
            nonlocal current_paragraph, p_start_offset
            if current_paragraph:
                p_text = "\n".join(current_paragraph).strip()
                if p_text:
                    blocks.append({
                        "type": "paragraph",
                        "text": p_text,
                        "start_char": p_start_offset,
                        "end_char": end_offset,
                        "active_header": current_header,
                    })
                current_paragraph = []

        for line in lines:
            stripped = line.strip()
            header_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
            line_len = len(line) + 1  # include newline char

            if header_match:
                flush_paragraph(current_offset)
                level = len(header_match.group(1))
                header_text = header_match.group(2).strip()
                current_header = header_text
                blocks.append({
                    "type": "header",
                    "level": level,
                    "text": stripped,
                    "header_text": header_text,
                    "start_char": current_offset,
                    "end_char": current_offset + len(line),
                    "active_header": current_header,
                })
                current_offset += line_len
                p_start_offset = current_offset
            elif not stripped:
                flush_paragraph(current_offset)
                current_offset += line_len
                p_start_offset = current_offset
            else:
                if not current_paragraph:
                    p_start_offset = current_offset
                current_paragraph.append(line)
                current_offset += line_len

        flush_paragraph(current_offset)
        return blocks

    def split_long_block(self, block_text: str, max_size: int) -> List[str]:
        """Split an oversized paragraph at sentence boundaries."""
        sentences = re.split(r'(?<=[.!?。！？\n])\s+', block_text)
        sub_blocks: List[str] = []
        current_buf: List[str] = []
        current_len = 0

        for sent in sentences:
            sent_len = len(sent)
            if current_len + sent_len > max_size and current_buf:
                sub_blocks.append(" ".join(current_buf))
                current_buf = [sent]
                current_len = sent_len
            else:
                current_buf.append(sent)
                current_len += sent_len + 1

        if current_buf:
            sub_blocks.append(" ".join(current_buf))

        return sub_blocks

    def chunk_document(
        self,
        text: str,
        source_doc: Optional[str] = None
    ) -> List[SemanticChunk]:
        """
        Segment input text into ordered SemanticChunk objects.
        Ensures topic boundary preservation and zero redundant tokens.
        """
        if not text or not text.strip():
            return []

        blocks = self.segment_into_blocks(text)
        if not blocks:
            return []

        chunks: List[SemanticChunk] = []
        acc_text: List[str] = []
        acc_start = blocks[0]["start_char"]
        acc_end = blocks[0]["end_char"]
        acc_header = blocks[0].get("active_header")
        acc_cohesions: List[float] = []

        chunk_counter = 1

        def finalize_chunk(text_pieces: List[str], start_c: int, end_c: int, header: Optional[str], cohesions: List[float]):
            nonlocal chunk_counter
            merged_text = "\n\n".join(text_pieces).strip()
            if not merged_text:
                return

            avg_cohesion = sum(cohesions) / len(cohesions) if cohesions else 1.0
            word_count = len(re.findall(r'\w+', merged_text))
            token_estimate = int(word_count * 1.3) or len(merged_text) // 4 or 1

            chunk_obj = SemanticChunk(
                chunk_id=f"chunk_{chunk_counter:04d}",
                text=merged_text,
                start_char=start_c,
                end_char=end_c,
                token_count=token_estimate,
                section_header=header,
                cohesion_score=round(avg_cohesion, 4),
                source_doc=source_doc,
                metadata={
                    "block_count": len(text_pieces),
                    "redundant_tokens": 0,
                }
            )
            chunks.append(chunk_obj)
            chunk_counter += 1

        for i, block in enumerate(blocks):
            b_text = block["text"]
            b_type = block["type"]
            b_header = block.get("active_header")
            b_start = block["start_char"]
            b_end = block["end_char"]

            # If current block is a structural header and we want to preserve section boundaries
            if b_type == "header" and self.preserve_headers:
                if acc_text:
                    finalize_chunk(acc_text, acc_start, acc_end, acc_header, acc_cohesions)
                    acc_text = []
                    acc_cohesions = []
                    acc_start = b_start
                acc_header = block.get("header_text")
                acc_text.append(b_text)
                acc_end = b_end
                continue

            # Check if block itself is too large for max_chunk_size
            if len(b_text) > self.max_chunk_size:
                sub_blocks = self.split_long_block(b_text, self.target_chunk_size)
                for sub in sub_blocks:
                    if acc_text and (sum(len(t) for t in acc_text) + len(sub) > self.target_chunk_size):
                        finalize_chunk(acc_text, acc_start, acc_end, acc_header, acc_cohesions)
                        acc_text = []
                        acc_cohesions = []
                        acc_start = b_start
                    acc_text.append(sub)
                    acc_end = b_end
                continue

            # Calculate cohesion with existing accumulator
            current_acc_size = sum(len(t) for t in acc_text)
            if acc_text:
                last_block_text = acc_text[-1]
                cohesion = self.calculate_cohesion(last_block_text, b_text)
                acc_cohesions.append(cohesion)
            else:
                cohesion = 1.0

            # Decision to flush accumulator:
            # 1. Total size exceeds max_chunk_size
            # 2. Total size reaches target_chunk_size AND cohesion to next block is low (topic transition)
            exceeds_max = (current_acc_size + len(b_text) > self.max_chunk_size)
            topic_shift = (current_acc_size >= self.target_chunk_size and cohesion < self.cohesion_threshold)

            if acc_text and (exceeds_max or topic_shift):
                finalize_chunk(acc_text, acc_start, acc_end, acc_header, acc_cohesions)
                acc_text = [b_text]
                acc_start = b_start
                acc_end = b_end
                acc_header = b_header
                acc_cohesions = []
            else:
                if not acc_text:
                    acc_start = b_start
                    acc_header = b_header
                acc_text.append(b_text)
                acc_end = b_end

        if acc_text:
            finalize_chunk(acc_text, acc_start, acc_end, acc_header, acc_cohesions)

        return chunks

    def get_chunks_as_strings(self, text: str) -> List[str]:
        """Convenience method returning plain string chunks."""
        return [c.text for c in self.chunk_document(text)]
