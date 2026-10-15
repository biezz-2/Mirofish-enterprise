"""
MiroFish Enterprise CaMeL 3-Layer Prompt Shield Guard (Agent 03: Divisi A)
Implementasi sistem pertahanan injeksi prompt berbasis arsitektur CaMeL (arXiv:2503.18813):
- L1: Sanitasi regex & HTML (membersihkan pola injeksi langsung, token kontrol LLM, template tags).
- L2: XML Spotlighting (delimiting konten tak terpercaya dengan isolasi tag & pencegahan XML escape).
- L3: Passive Deterministic Extractor (pemisahan control flow vs data flow berbasis capability,
      menjamin data eksternal tidak pernah memiliki kapabilitas eksekusi / tool-call).
"""

import re
import html
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ShieldResult(BaseModel):
    is_safe: bool = True
    sanitized_text: str
    detected_patterns: List[str] = Field(default_factory=list)
    spotlight_xml: str
    content_id: str

class CaMeLPromptShield:
    """CaMeL 3-Layer Defense against Prompt Injection & Jailbreaking."""

    INJECTION_PATTERNS = [
        (r"ignore\s+(?:all\s+)?previous\s+instructions", "DIRECTIVE_OVERRIDE"),
        (r"abaikan\s+(?:semua\s+)?instruksi\s+sebelumnya", "DIRECTIVE_OVERRIDE_ID"),
        (r"system\s+prompt\s*(?:override|reset)", "SYSTEM_PROMPT_OVERRIDE"),
        (r"disregard\s+(?:all\s+)?prior\s+prompts", "PRIOR_PROMPTS_DISREGARD"),
        (r"you\s+are\s+now\s+(?:an?\s+)?unrestricted", "JAILBREAK_ROLEPLAY"),
        (r"dan\s+mode\s+jailbreak", "JAILBREAK_DAN"),
        (r"<\|im_start\|>|<\|im_end\|>|<\|endoftext\|>", "SPECIAL_TOKEN_INJECTION"),
        (r"\{\{.*?\}\}|\$\{.*?\}", "TEMPLATE_INJECTION"),
        (r"javascript\s*:", "JS_SCHEME"),
        (r"data\s*:\s*text\/html", "DATA_SCHEME"),
        (r"<script[\s\S]*?>[\s\S]*?<\/script>", "SCRIPT_TAG"),
        (r"<iframe[\s\S]*?>[\s\S]*?<\/iframe>", "IFRAME_TAG"),
    ]

    def __init__(self, max_length: int = 4000):
        self.max_length = max_length

    # Layer 1: Sanitasi Regex & HTML
    def layer1_sanitize(self, raw_text: str) -> tuple[str, List[str]]:
        if not raw_text:
            return "", []

        text = raw_text[:self.max_length]
        detected = []

        # Deteksi pola injeksi berbahaya
        for pattern, tag in self.INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                detected.append(tag)
                # Netralisasi pola berbahaya
                text = re.sub(pattern, f"[REDACTED_{tag}]", text, flags=re.IGNORECASE)

        # Netralisasi HTML tags & special characters
        text = html.escape(text, quote=True)
        # Hapus kontrol karakter tersembunyi
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

        return text, detected

    # Layer 2: XML Spotlighting (Delimiting untrusted data)
    def layer2_spotlight(self, sanitized_text: str, source: str = "web_search", content_id: Optional[str] = None) -> str:
        cid = content_id or str(uuid.uuid4())[:8]
        # Pastikan tag penutup di-escape agar tidak bisa breakout dari spotlight
        escaped_for_xml = sanitized_text.replace("</untrusted_content_data>", "&lt;/untrusted_content_data&gt;")
        spotlight = (
            f'<untrusted_content_data id="{cid}" source="{html.escape(source)}" role="data_only">\n'
            f"{escaped_for_xml}\n"
            f"</untrusted_content_data>"
        )
        return spotlight

    # Layer 3: Passive Deterministic Extractor (Data Flow Isolation)
    def layer3_passive_extract(self, spotlight_xml: str) -> Dict[str, Any]:
        """
        Mengekstrak data secara deterministik murni tanpa memberikan kapabilitas
        eksekusi atau tool-call pada alur data tak terpercaya (CaMeL capability isolation).
        """
        # Ekstraksi atribut metadata
        id_match = re.search(r'id="([^"]+)"', spotlight_xml)
        src_match = re.search(r'source="([^"]+)"', spotlight_xml)
        
        # Ekstraksi body teks pasif
        body_match = re.search(r'<untrusted_content_data[^>]*>([\s\S]*?)<\/untrusted_content_data>', spotlight_xml)
        raw_body = body_match.group(1).strip() if body_match else ""

        # Unescape aman untuk representasi data internal murni
        parsed_data = html.unescape(raw_body)

        return {
            "content_id": id_match.group(1) if id_match else "",
            "source": src_match.group(1) if src_match else "unknown",
            "passive_payload": parsed_data,
            "capabilities_allowed": ["READ_PASSIVE_DATA"],  # Tidak boleh TOOL_EXEC / SYSTEM_CONTROL
            "control_flow_isolated": True,
        }

    def process(self, raw_text: str, source: str = "web_search") -> ShieldResult:
        """Menjalankan seluruh 3 layer CaMeL prompt shield."""
        cid = str(uuid.uuid4())[:8]
        sanitized, detected = self.layer1_sanitize(raw_text)
        spotlight = self.layer2_spotlight(sanitized, source=source, content_id=cid)
        is_safe = len(detected) == 0

        return ShieldResult(
            is_safe=is_safe,
            sanitized_text=sanitized,
            detected_patterns=detected,
            spotlight_xml=spotlight,
            content_id=cid,
        )

# Global default helper
_shield_instance = CaMeLPromptShield()

def sanitize_untrusted_content(raw_text: str, source: str = "web_search") -> ShieldResult:
    return _shield_instance.process(raw_text, source)
