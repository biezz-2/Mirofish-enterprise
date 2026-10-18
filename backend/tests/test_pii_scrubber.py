"""
Unit tests untuk Modul Sanitasi PII MiroFish Enterprise (backend/app/services/pii_scrubber.py).
Memverifikasi kepatuhan terhadap UU No. 27 Tahun 2022 (UU PDP):
1. Pembersihan NIK 16 digit.
2. Pembersihan nomor HP Indonesia (+62 dan 08xx).
3. Pembersihan email dan nomor kartu kredit / rekening finansial.
4. Idempotensi pembersihan teks.
"""

import pytest
from app.services.pii_scrubber import (
    PIIScrubber,
    scrub_pii,
    scrub_nik,
    scrub_phone,
    scrub_email,
    scrub_financial,
    scrub_credit_card,
    scrub_names,
    TOKEN_NIK,
    TOKEN_PHONE,
    TOKEN_EMAIL,
    TOKEN_FINANCIAL,
    TOKEN_NAME,
)


# ============================================================================
# 1. Tes Pembersihan NIK 16 Digit
# ============================================================================

def test_scrub_nik_16_digit_raw():
    """Memastikan NIK 16 digit mentah disanitasi menjadi [REDACTED_NIK]."""
    raw_nik = "3171010101900001"
    assert scrub_nik(raw_nik) == TOKEN_NIK
    assert scrub_pii(raw_nik) == TOKEN_NIK


def test_scrub_nik_with_contextual_keywords():
    """Memastikan NIK dengan prefix seperti 'NIK:', 'No. KTP', 'Nomor KTP' disanitasi."""
    text1 = "NIK: 3201012345670001 terdaftar di Disdukcapil."
    assert scrub_nik(text1) == f"NIK: {TOKEN_NIK} terdaftar di Disdukcapil."
    assert scrub_pii(text1) == f"NIK: {TOKEN_NIK} terdaftar di Disdukcapil."

    text2 = "No. KTP 3578011205850002 milik warga Surabaya."
    assert scrub_nik(text2) == f"No. KTP {TOKEN_NIK} milik warga Surabaya."
    assert scrub_pii(text2) == f"No. KTP {TOKEN_NIK} milik warga Surabaya."


def test_scrub_nik_with_separators():
    """Memastikan NIK dengan pemisah tanda hubung atau spasi disanitasi."""
    formatted_664 = "317101-010190-0001"
    assert scrub_nik(formatted_664) == TOKEN_NIK

    formatted_4444 = "3171-0101-0190-0001"
    assert scrub_nik(formatted_4444) == TOKEN_NIK


def test_scrub_nik_embedded_in_narrative():
    """Memastikan NIK yang disematkan dalam narasi web/dokumen disanitasi."""
    narrative = (
        "Berdasarkan investigasi, saksi memiliki NIK 3273010102920003 dan bertempat "
        "tinggal di Bandung sejak tahun 2018."
    )
    result = scrub_pii(narrative)
    assert TOKEN_NIK in result
    assert "3273010102920003" not in result


# ============================================================================
# 2. Tes Pembersihan Nomor HP Indonesia (+62 dan 08xx)
# ============================================================================

def test_scrub_phone_plus_62_formats():
    """Memastikan nomor telepon format internasional (+62 / 62) disanitasi."""
    samples = [
        "+6281234567890",
        "+62 812-3456-7890",
        "+62-812-3456-7890",
        "+62 812 3456 7890",
        "6281234567890",
    ]
    for sample in samples:
        scrubbed = scrub_phone(sample)
        assert scrubbed == TOKEN_PHONE, f"Gagal pada format: {sample} -> {scrubbed}"
        assert scrub_pii(sample) == TOKEN_PHONE


def test_scrub_phone_08xx_domestic_formats():
    """Memastikan nomor HP format domestik 08xx disanitasi."""
    samples = [
        "081234567890",
        "0812-3456-7890",
        "0812 3456 7890",
        "0857-1234-5678",
        "089612345678",
        "08781234567",
    ]
    for sample in samples:
        scrubbed = scrub_phone(sample)
        assert scrubbed == TOKEN_PHONE, f"Gagal pada format: {sample} -> {scrubbed}"
        assert scrub_pii(sample) == TOKEN_PHONE


def test_scrub_phone_embedded_in_text():
    """Memastikan nomor HP dalam kalimat percakapan disanitasi."""
    text = "Silakan hubungi layanan pelanggan via WhatsApp di 081234567890 atau kantor di +62 811-2233-4455."
    cleaned = scrub_pii(text)
    assert "081234567890" not in cleaned
    assert "+62 811-2233-4455" not in cleaned
    assert cleaned.count(TOKEN_PHONE) == 2


# ============================================================================
# 3. Tes Pembersihan Email dan Nomor Kartu Kredit / Finansial
# ============================================================================

def test_scrub_email_formats():
    """Memastikan alamat email dengan berbagai format domain disanitasi."""
    emails = [
        "user@example.com",
        "admin.staff@perusahaan.co.id",
        "john.doe+tag@sub.domain.org",
        "layanan-publik@kemenkes.go.id",
    ]
    for email in emails:
        assert scrub_email(email) == TOKEN_EMAIL
        text = f"Kirim berkas ke {email} untuk verifikasi."
        assert scrub_pii(text) == f"Kirim berkas ke {TOKEN_EMAIL} untuk verifikasi."


def test_scrub_credit_card_formatted():
    """Memastikan nomor kartu kredit dengan tanda hubung atau spasi disanitasi."""
    visa_mc = "4532-1234-5678-9012"
    assert scrub_financial(visa_mc) == TOKEN_FINANCIAL
    assert scrub_credit_card(visa_mc) == TOKEN_FINANCIAL
    assert scrub_pii(visa_mc) == TOKEN_FINANCIAL

    card_space = "4532 1234 5678 9012"
    assert scrub_financial(card_space) == TOKEN_FINANCIAL
    assert scrub_pii(card_space) == TOKEN_FINANCIAL

    amex = "3782-822463-10005"
    assert scrub_financial(amex) == TOKEN_FINANCIAL
    assert scrub_pii(amex) == TOKEN_FINANCIAL


def test_scrub_credit_card_unformatted_raw():
    """Memastikan nomor kartu kredit mentah 16 digit disanitasi."""
    raw_visa = "4532123456789012"
    assert scrub_financial(raw_visa) == TOKEN_FINANCIAL
    assert scrub_credit_card(raw_visa) == TOKEN_FINANCIAL


def test_scrub_bank_account_with_keywords():
    """Memastikan nomor rekening bank dengan kata kunci disanitasi."""
    samples = [
        ("Transfer ke rekening BCA 1234567890 sekarang.", f"Transfer ke rekening BCA {TOKEN_FINANCIAL} sekarang."),
        ("No. rek Mandiri 9876543210 atas nama PT MiroFish.", f"No. rek Mandiri {TOKEN_FINANCIAL} atas nama PT MiroFish."),
        ("Norek 5544332211 segera dikirim.", f"Norek {TOKEN_FINANCIAL} segera dikirim."),
    ]
    for text, expected in samples:
        res = scrub_pii(text)
        assert res == expected, f"Gagal pada rekening: {text} -> {res}"


# ============================================================================
# 4. Tes Idempotensi Pembersihan Teks
# ============================================================================

def test_scrub_pii_idempotency_single_string():
    """
    Idempotensi matematis: scrub_pii(scrub_pii(text)) == scrub_pii(text).
    Menjamin token pengganti tidak bermutasi atau merusak teks pada pemindaian ulang.
    """
    complex_text = (
        "Pengguna Bpk. Budi Santoso dengan NIK 3171010101900001 memiliki kontak "
        "HP 0812-3456-7890 dan email budi.santoso@example.com. Kartu kredit "
        "4532-1234-5678-9012 dan rekening BRI 12345678901 terdaftar pada profil."
    )

    pass1 = scrub_pii(complex_text)
    pass2 = scrub_pii(pass1)
    pass3 = scrub_pii(pass2)
    pass4 = scrub_pii(pass3)

    assert pass1 == pass2, "Idempotensi gagal pada pass kedua"
    assert pass2 == pass3, "Idempotensi gagal pada pass ketiga"
    assert pass3 == pass4, "Idempotensi gagal pada pass keempat"

    # Verifikasi seluruh token pengganti ada dan data asli hilang
    assert TOKEN_NAME in pass1
    assert TOKEN_NIK in pass1
    assert TOKEN_PHONE in pass1
    assert TOKEN_EMAIL in pass1
    assert TOKEN_FINANCIAL in pass1

    assert "3171010101900001" not in pass1
    assert "0812-3456-7890" not in pass1
    assert "budi.santoso@example.com" not in pass1
    assert "4532-1234-5678-9012" not in pass1
    assert "12345678901" not in pass1


def test_scrub_pii_tokens_invariance():
    """Memastikan token pengganti itu sendiri kebal terhadap scrubbing ulang."""
    tokens_text = f"{TOKEN_NIK} {TOKEN_PHONE} {TOKEN_EMAIL} {TOKEN_FINANCIAL} {TOKEN_NAME}"
    assert scrub_pii(tokens_text) == tokens_text
    assert scrub_nik(TOKEN_NIK) == TOKEN_NIK
    assert scrub_phone(TOKEN_PHONE) == TOKEN_PHONE
    assert scrub_email(TOKEN_EMAIL) == TOKEN_EMAIL
    assert scrub_financial(TOKEN_FINANCIAL) == TOKEN_FINANCIAL


# ============================================================================
# 5. Tes Nama Pribadi dan Fitur Utilitas Tambahan
# ============================================================================

def test_scrub_personal_names():
    """Memastikan nama dengan sapaan/gelar resmi atau custom names disanitasi."""
    text1 = "Laporan diserahkan kepada Bpk. Joko Widodo di Istana."
    assert scrub_names(text1) == f"Laporan diserahkan kepada Bpk. {TOKEN_NAME} di Istana."

    text2 = "Dikonfirmasi oleh Ibu Sri Mulyani selaku Menteri."
    assert scrub_names(text2) == f"Dikonfirmasi oleh Ibu {TOKEN_NAME} selaku Menteri."

    # Custom names
    custom_text = "Target intelijen adalah John Doe dan Alice Smith."
    cleaned = scrub_names(custom_text, names=["John Doe", "Alice Smith"])
    assert cleaned == f"Target intelijen adalah {TOKEN_NAME} dan {TOKEN_NAME}."


def test_pii_detection_and_cleanliness():
    """Memastikan deteksi metrik PII dan pengecekan kebersihan teks berfungsi."""
    dirty = "Kontak: 081234567890, email: info@test.com, NIK: 3171010101900001"
    counts = PIIScrubber.detect_pii(dirty)
    assert counts["phone"] >= 1
    assert counts["email"] >= 1
    assert counts["nik"] >= 1
    assert not PIIScrubber.is_clean(dirty)

    clean_text = PIIScrubber.scrub(dirty)
    assert PIIScrubber.is_clean(clean_text)


def test_scrub_dict_nested():
    """Memastikan struktur dictionary bersarang dibersihkan secara rekursif."""
    data = {
        "user": {
            "name": "Bpk. Ahmad Dahlan",
            "contact": {
                "email": "ahmad@foundation.id",
                "phone": "+6281234567890",
            },
            "credentials": {
                "nik": "3171010101900001",
                "card": "4532-1234-5678-9012"
            }
        },
        "tags": ["public", "verified"]
    }

    sanitized = PIIScrubber.scrub_dict(data)
    assert sanitized["user"]["name"] == f"Bpk. {TOKEN_NAME}"
    assert sanitized["user"]["contact"]["email"] == TOKEN_EMAIL
    assert sanitized["user"]["contact"]["phone"] == TOKEN_PHONE
    assert sanitized["user"]["credentials"]["nik"] == TOKEN_NIK
    assert sanitized["user"]["credentials"]["card"] == TOKEN_FINANCIAL
    assert sanitized["tags"] == ["public", "verified"]


def test_non_pii_strings_preservation():
    """Memastikan data teknis non-PII (timestamp, UUID, metrik, skor) tidak rusak."""
    tech_text = (
        "Server status 200 OK pada 2026-10-18T14:30:00Z. "
        "Project ID proj_5e996d7cdf4b memiliki 42 nodes dan 108 edges. "
        "Confidence score: 0.95, latency: 120ms."
    )
    assert scrub_pii(tech_text) == tech_text
