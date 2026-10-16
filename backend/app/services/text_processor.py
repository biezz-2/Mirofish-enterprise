"""
文本处理服务
Mendukung pemotongan teks adaptif semantik berbasis kohesi topikal dan pemisahan batas paragraf.
"""

from typing import List, Optional, Dict, Any
from ..utils.file_parser import FileParser, split_text_into_chunks
from .adaptive_chunker import AdaptiveSemanticChunker
from ..models.graphrag_ontology import SemanticChunk


class TextProcessor:
    """文本处理器"""
    
    @staticmethod
    def extract_from_files(file_paths: List[str]) -> str:
        """从多个文件提取文本"""
        return FileParser.extract_from_multiple(file_paths)
    
    @staticmethod
    def split_text(
        text: str,
        chunk_size: int = 500,
        overlap: int = 50,
        adaptive: bool = False
    ) -> List[str]:
        """
        分割文本
        
        Args:
            text: 原始文本
            chunk_size: 块大小
            overlap: 重叠大小
            adaptive: 是否使用自适应语义切分
            
        Returns:
            文本块列表
        """
        if adaptive:
            chunker = AdaptiveSemanticChunker(
                target_chunk_size=chunk_size,
                max_chunk_size=chunk_size + overlap
            )
            return chunker.get_chunks_as_strings(text)
        return split_text_into_chunks(text, chunk_size, overlap)

    @staticmethod
    def split_text_adaptive(
        text: str,
        target_chunk_size: int = 800,
        min_chunk_size: int = 200,
        max_chunk_size: int = 1500,
        cohesion_threshold: float = 0.15,
        preserve_headers: bool = True,
        source_doc: Optional[str] = None
    ) -> List[SemanticChunk]:
        """
        Adaptive Semantic Text Chunking based on paragraph boundaries and topical cohesion.
        
        Returns:
            List of structured SemanticChunk objects with chunk_id, offsets, and metadata.
        """
        chunker = AdaptiveSemanticChunker(
            target_chunk_size=target_chunk_size,
            min_chunk_size=min_chunk_size,
            max_chunk_size=max_chunk_size,
            cohesion_threshold=cohesion_threshold,
            preserve_headers=preserve_headers
        )
        return chunker.chunk_document(text, source_doc=source_doc)
    
    @staticmethod
    def preprocess_text(text: str) -> str:
        """
        预处理文本
        - 移除多余空白
        - 标准化换行
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        import re
        
        # 标准化换行
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 移除连续空行（保留最多两个换行）
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 移除行首行尾空白
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()
    
    @staticmethod
    def get_text_stats(text: str) -> dict:
        """获取文本统计信息"""
        return {
            "total_chars": len(text),
            "total_lines": text.count('\n') + 1,
            "total_words": len(text.split()),
        }
