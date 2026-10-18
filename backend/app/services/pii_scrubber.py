"""
Modul Sanitasi PII (Personally Identifiable Information) MiroFish Enterprise.
Kepatuhan terhadap UU No. 27 Tahun 2022 tentang Pelindungan Data Pribadi (UU PDP).

Menyediakan deteksi otomatis dan penyamaran (scrubbing) token anonim untuk:
- NIK (Nomor Induk Kependudukan - 16 digit) -> [REDACTED_NIK]
- Nomor Telepon Indonesia (+62 / 08xx) -> [REDACTED_PHONE]
- Alamat Email -> [REDACTED_EMAIL]
- Rekening Bank / Nomor Kartu Kredit -> [REDACTED_FINANCIAL]
- Mention Nama Pribadi Spesifik -> [REDACTED_NAME]

Idempotent: scrub_pii(scrub_pii(text)) == scrub_pii(text).
"""

import re
from typing import Dict, Any, List, Optional

# Token pengganti anonim sesuai spesifikasi UU PDP MiroFish Enterprise
TOKEN_NIK = "[REDACTED_NIK]"
TOKEN_PHONE = "[REDACTED_PHONE]"
TOKEN_EMAIL = "[REDACTED_EMAIL]"
TOKEN_FINANCIAL = "[REDACTED_FINANCIAL]"
TOKEN_NAME = "[REDACTED_NAME]"

# 1. Regex Kartu Kredit & Keuangan
_CARD_FORMATTED = re.compile(r"\b(?:\d{4}[-\s]){3}\d{4}\b")
_AMEX_FORMATTED = re.compile(r"\b3[47]\d{2}[-\s]\d{6}[-\s]\d{5}\b")
_CARD_VISA_RAW = re.compile(r"\b4\d{15}\b")
_CARD_MASTERCARD_RAW = re.compile(
    r"\b(?:5[1-5]\d{2}|222[1-9]|22[3-9]\d|2[3-6]\d{2}|27[01]\d|2720)\d{12}\b"
)
_CARD_AMEX_RAW = re.compile(r"\b3[47]\d{13}\b")
_CARD_DISCOVER_RAW = re.compile(r"\b6(?:011|5\d{2})\d{12}\b" )
_FINANCIAL_KEYWORD_CARD = re.compile(
    r"(?i)\b(?:kartu\s*kredit|credit\s*card|cc|visa|mastercard|amex)\s*[:#]?\s*([0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{3,4}|[0-9]{13,19})\b"
)
_FINANCIAL_KEYWORD_ACC = re.compile(
    r"(?i)\b(?:rekening|no\.?\s*rek(?:ening)?|norek|bank\s*account|account\s*number)(?:\s+[a-zA-Z]{2,10})?\s*[:#]?\s*([0-9]{8,20})\b"
)

# 2. Regex NIK (16 digit)
_NIK_CONTEXTUAL = re.compile(
    r"(?i)\b(?:nik|no\.?\s*ktp|nomor\s*ktp|ktp|identitas)\s*[:#]?\s*([0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}|[0-9]{6}[-\s]?[0-9]{6}[-\s]?[0-9]{4}|[0-9]{16})\b"
)
_NIK_FORMATTED_664 = re.compile(r"\b[1-9]\d{5}[-\s]\d{6}[-\s]\d{4}\b")
_NIK_FORMATTED_4444 = re.compile(r"\b[1-9]\d{3}[-\s]\d{4}[-\s]\d{4}[-\s]\d{4}\b")
_NIK_RAW = re.compile(r"\b[1-9]\d{15}\b")
_NIK_GENERIC_16 = re.compile(r"\b\d{16}\b")

# 3. Regex Nomor Telepon Indonesia (+62 / 08xx)
_PHONE_INDONESIA = re.compile(
    r"(?i)(?:(?<=\s)|(?<=[(>\"'`:;,-])|^)(?:\+?62[-\s.]?|0)8[1-9][0-9](?:[-\s.]?[0-9]{2,5}){2,4}\b"
)
_PHONE_LANDLINE = re.compile(
    r"(?i)(?:(?<=\s)|(?<=[(>\"'`:;,-])|^)(?:\+?62[-\s.]?|0)(?:2[1-9]|[3-9][0-9])(?:[-\s.]?[0-9]{3,4}){2}\b"
)
_PHONE_GENERIC = re.compile(
    r"(?i)\b(?:telp|telepon|phone|hp|handphone|wa|whatsapp)\s*[:#]?\s*(\+?[0-9][0-9\s.-]{7,15}[0-9])\b"
)

# 4. Regex Email
_EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

# 5. Regex Nama Pribadi dengan Sapaan/Gelar
_HONORIFICS_NAME = re.compile(
    r"\b(?:[bB]pk|[bB]apak|[iI]bu|[sS]dr|[sS]dri|[tT]n|[nN]y|[nN]n|[mM]r|[mM]rs|[mM]s|[pP]rof|[dD]r|[dD]rg)\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b"
)


class PIIScrubber:
    """Mesin pembersih PII (Personally Identifiable Information) berbasis aturan deterministik."""

    @classmethod
    def scrub_financial(cls, text: str) -> str:
        """Pembersihan nomor kartu kredit dan rekening bank -> [REDACTED_FINANCIAL]."""
        if not text:
            return "" if text is None else text

        res = _CARD_FORMATTED.sub(TOKEN_FINANCIAL, text)
        res = _AMEX_FORMATTED.sub(TOKEN_FINANCIAL, res)
        res = _CARD_VISA_RAW.sub(TOKEN_FINANCIAL, res)
        res = _CARD_MASTERCARD_RAW.sub(TOKEN_FINANCIAL, res)
        res = _CARD_AMEX_RAW.sub(TOKEN_FINANCIAL, res)
        res = _CARD_DISCOVER_RAW.sub(TOKEN_FINANCIAL, res)

        def _sub_card(match):
            full = match.group(0)
            digits = match.group(1)
            return full.replace(digits, TOKEN_FINANCIAL)

        res = _FINANCIAL_KEYWORD_CARD.sub(_sub_card, res)
        res = _FINANCIAL_KEYWORD_ACC.sub(_sub_card, res)
        return res

    @classmethod
    def scrub_nik(cls, text: str) -> str:
        """Pembersihan NIK 16 digit -> [REDACTED_NIK]."""
        if not text:
            return "" if text is None else text

        def _sub_nik(match):
            full = match.group(0)
            digits = match.group(1)
            return full.replace(digits, TOKEN_NIK)

        res = _NIK_CONTEXTUAL.sub(_sub_nik, text)
        res = _NIK_FORMATTED_664.sub(TOKEN_NIK, res)
        res = _NIK_FORMATTED_4444.sub(TOKEN_NIK, res)
        res = _NIK_RAW.sub(TOKEN_NIK, res)
        res = _NIK_GENERIC_16.sub(TOKEN_NIK, res)
        return res

    @classmethod
    def scrub_phone(cls, text: str) -> str:
        """Pembersihan nomor HP Indonesia (+62 / 08xx) dan telepon -> [REDACTED_PHONE]."""
        if not text:
            return "" if text is None else text

        def _sub_phone(match):
            full = match.group(0)
            digits = match.group(1)
            return full.replace(digits, TOKEN_PHONE)

        res = _PHONE_GENERIC.sub(_sub_phone, text)
        res = _PHONE_INDONESIA.sub(TOKEN_PHONE, res)
        res = _PHONE_LANDLINE.sub(TOKEN_PHONE, res)
        return res

    @classmethod
    def scrub_email(cls, text: str) -> str:
        """Pembersihan alamat email -> [REDACTED_EMAIL]."""
        if not text:
            return "" if text is None else text
        return _EMAIL_PATTERN.sub(TOKEN_EMAIL, text)

    @classmethod
    def scrub_names(cls, text: str, names: Optional[List[str]] = None) -> str:
        """Pembersihan nama pribadi spesifik dengan gelar/sapaan -> [REDACTED_NAME]."""
        if not text:
            return "" if text is None else text

        res = text
        if names:
            for name in names:
                if name and len(name.strip()) >= 2:
                    pattern = re.compile(rf"\b{re.escape(name.strip())}\b", re.IGNORECASE)
                    res = pattern.sub(TOKEN_NAME, res)

        def _sub_honorific(match):
            full = match.group(0)
            name_part = match.group(1)
            return full.replace(name_part, TOKEN_NAME)

        res = _HONORIFICS_NAME.sub(_sub_honorific, res)
        return res

    @classmethod
    def scrub(
        cls,
        text: str,
        redact_names: bool = True,
        custom_names: Optional[List[str]] = None,
    ) -> str:
        """
        Pembersihan komprehensif seluruh PII.
        Urutan deterministik:
        1. Contextual NIK
        2. Financial (Kartu Kredit & Rekening Bank)
        3. Standalone NIK (16 digit)
        4. Telepon (+62 / 08xx)
        5. Email
        6. Nama Pribadi
        """
        if not text:
            return "" if text is None else text

        result = str(text)

        # 1. Contextual NIK
        def _sub_nik_ctx(match):
            full = match.group(0)
            digits = match.group(1)
            return full.replace(digits, TOKEN_NIK)

        result = _NIK_CONTEXTUAL.sub(_sub_nik_ctx, result)

        # 2. Financial
        result = cls.scrub_financial(result)

        # 3. NIK (Standalone/Formatted)
        result = cls.scrub_nik(result)

        # 4. Telepon
        result = cls.scrub_phone(result)

        # 5. Email
        result = cls.scrub_email(result)

        # 6. Nama
        if redact_names:
            result = cls.scrub_names(result, names=custom_names)

        return result

    @classmethod
    def detect_pii(cls, text: str) -> Dict[str, int]:
        """Deteksi jumlah kemunculan tiap kategori PII tanpa mengekspos isi data sensitif."""
        if not text:
            return {"nik": 0, "phone": 0, "email": 0, "financial": 0, "name": 0}

        counts = {
            "financial": len(_CARD_FORMATTED.findall(text))
            + len(_AMEX_FORMATTED.findall(text))
            + len(_CARD_VISA_RAW.findall(text))
            + len(_CARD_MASTERCARD_RAW.findall(text))
            + len(_FINANCIAL_KEYWORD_CARD.findall(text))
            + len(_FINANCIAL_KEYWORD_ACC.findall(text)),
            "nik": len(_NIK_CONTEXTUAL.findall(text))
            + len(_NIK_FORMATTED_664.findall(text))
            + len(_NIK_FORMATTED_4444.findall(text))
            + len(_NIK_RAW.findall(text)),
            "phone": len(_PHONE_INDONESIA.findall(text))
            + len(_PHONE_LANDLINE.findall(text)),
            "email": len(_EMAIL_PATTERN.findall(text)),
            "name": len(_HONORIFICS_NAME.findall(text)),
        }
        return counts

    @classmethod
    def is_clean(cls, text: str) -> bool:
        """Memeriksa apakah teks bebas dari PII yang belum disanitasi."""
        counts = cls.detect_pii(text)
        return sum(counts.values()) == 0

    @classmethod
    def scrub_dict(
        cls,
        data: Any,
        redact_names: bool = True,
        custom_names: Optional[List[str]] = None,
    ) -> Any:
        """Rekursif membersihkan objek dictionary atau list dari PII."""
        if isinstance(data, str):
            return cls.scrub(data, redact_names=redact_names, custom_names=custom_names)
        elif isinstance(data, dict):
            return {
                k: cls.scrub_dict(v, redact_names=redact_names, custom_names=custom_names)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [
                cls.scrub_dict(item, redact_names=redact_names, custom_names=custom_names)
                for item in data
            ]
        return data


# Fungsi publik mandiri
def scrub_pii(
    text: str,
    redact_names: bool = True,
    custom_names: Optional[List[str]] = None,
) -> str:
    return PIIScrubber.scrub(text, redact_names=redact_names, custom_names=custom_names)


def scrub_nik(text: str) -> str:
    return PIIScrubber.scrub_nik(text)


def scrub_phone(text: str) -> str:
    return PIIScrubber.scrub_phone(text)


def scrub_email(text: str) -> str:
    return PIIScrubber.scrub_email(text)


def scrub_financial(text: str) -> str:
    return PIIScrubber.scrub_financial(text)


def scrub_credit_card(text: str) -> str:
    return PIIScrubber.scrub_financial(text)


def scrub_names(text: str, names: Optional[List[str]] = None) -> str:
    return PIIScrubber.scrub_names(text, names=names)
