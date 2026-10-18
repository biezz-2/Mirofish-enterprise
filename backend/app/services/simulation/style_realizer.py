# backend/app/services/simulation/style_realizer.py
"""
Style Realizer: Template Prompt Thread Transcript dengan Few-Shot Retrieval
Menggantikan instruksi mentah kaku dengan 3-5 contoh percakapan riil per register dan topik
untuk menghasilkan gaya bahasa natural menyerupai netizen Indonesia.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.services.simulation.intent_sampler import IntentType
from app.services.simulation.persona_store import Persona


@dataclass
class ConversationSample:
    """Contoh riil interaksi percakapan few-shot."""
    register: str
    topic: str
    intent: str
    context: str
    response: str


# Bank Data Few-Shot Percakapan Riil
FEW_SHOT_CORPUS: List[ConversationSample] = [
    # Register: formal
    ConversationSample(
        register="formal",
        topic="kebijakan_publik",
        intent="Agree/Support",
        context="Pemerintah mengumumkan kenaikan anggaran riset dan inovasi daerah.",
        response="Langkah ini patut diapresiasi secara objektif. Transparansi alokasi dana dan evaluasi berbasis output riset harus dikawal bersama.",
    ),
    ConversationSample(
        register="formal",
        topic="kebijakan_publik",
        intent="Disagree/Counter",
        context="Rencana penerapan tarif pajak baru untuk sektor UMKM digital.",
        response="Kebijakan fiskal tersebut berisiko menghambat pertumbuhan industri rintisan lokal jika tidak disertai masa transisi yang memadai.",
    ),
    ConversationSample(
        register="formal",
        topic="pendidikan",
        intent="Clarification/Question",
        context="Sosialisasi skema akreditasi perguruan tinggi terbaru tahun 2026.",
        response="Apakah terdapat ketentuan khusus mengenai konversi publikasi terindeks bagi perguruan tinggi swasta di luar Pulau Jawa?",
    ),
    ConversationSample(
        register="formal",
        topic="ekonomi",
        intent="Nuanced Synthesis",
        context="Perdebatan efektivitas subsidi energi langsung vs harga pasar.",
        response="Pendekatan terpadu diperlukan: subsidi tepat sasaran melalui integrasi data kependudukan sembari menyiapkan bantalan sosial bagi kelompok rentan.",
    ),

    # Register: kasual santai
    ConversationSample(
        register="kasual santai",
        topic="kebijakan_publik",
        intent="Agree/Support",
        context="Transportasi umum di Jabodetabek makin rapi dan tepat waktu.",
        response="Bener bgt sih, sekarang naik KRL sama MRT jauh lebih nyaman ketimbang macet-macetan di jalan tol.",
    ),
    ConversationSample(
        register="kasual santai",
        topic="kebijakan_publik",
        intent="Disagree/Counter",
        context="Rencana penutupan jalan protokol untuk uji coba car free day baru.",
        response="Gak setuju sih klo ditutup pas hari kerja, jalan alternatifnya sempit dan malah bikin stuck parah.",
    ),
    ConversationSample(
        register="kasual santai",
        topic="teknologi",
        intent="Tangential/Derail",
        context="Update fitur AI baru di smartphone flagship terkini.",
        response="Btw baterainya tahan berapa jam klo fitur itu nyala terus? Soalnya hp skrg boros bgt klo dipake gaming.",
    ),
    ConversationSample(
        register="kasual santai",
        topic="sosial",
        intent="Emotional Outburst",
        context="Pelaku pungli parkir liar di minimarket kembali beraksi.",
        response="Asli kesel bgt liatnya, padahal udah dipasang spanduk gratis parkir tp tetep aja ada yg nongkrong nagih uang!",
    ),

    # Register: gaul jaksel
    ConversationSample(
        register="gaul jaksel",
        topic="kebijakan_publik",
        intent="Agree/Support",
        context="Program insentif kendaraan listrik diperluas ke transportasi massal.",
        response="Which is good sih ya, secara polusi udara udah alarming bgt. Hopefully ini beneran bisa shifting habit masyarakat.",
    ),
    ConversationSample(
        register="gaul jaksel",
        topic="sosial",
        intent="Disagree/Counter",
        context="Wacana larangan sistem kerja remote / WFH 100% dari asosiasi kantor.",
        response="Literally no point balik ke full WFO kalo performa tim fine-fine aja. Jujurly commuting 2 jam tiap hari tuh draining energy parah.",
    ),
    ConversationSample(
        register="gaul jaksel",
        topic="lifestyle",
        intent="Sarcasm/Meme",
        context="Tren beli kopi susu 60 ribu per cup demi prestise di co-working space.",
        response="Another day another lifestyle inflation ya bundles,, dompet tipis tapi aesthetic number one.",
    ),
    ConversationSample(
        register="gaul jaksel",
        topic="karier",
        intent="Nuanced Synthesis",
        context="Diskusi seputar work-life balance vs hustle culture di tech company.",
        response="Honestly speaking, ambisi itu perlu but mental health tetep priority. Harus bisa set boundaries yg sehat sih.",
    ),

    # Register: sarkastik
    ConversationSample(
        register="sarkastik",
        topic="kebijakan_publik",
        intent="Sarcasm/Meme",
        context="Janji perbaikan jalan rusak selesai dalam waktu 3 hari.",
        response="Iya percaya kok, nanti pas musim hujan jalannya berubah fungsi jadi kolam renang gratis warga sekitar.",
    ),
    ConversationSample(
        register="sarkastik",
        topic="kebijakan_publik",
        intent="Disagree/Counter",
        context="Rapat koordinasi anggaran studi banding ke luar negeri di masa efisiensi.",
        response="Luar biasa solutif ya para pejabat kita, studi banding ke Eropa biar bisa ngerasain langsung gimana dinginnya kritik rakyat.",
    ),
    ConversationSample(
        register="sarkastik",
        topic="teknologi",
        intent="Sarcasm/Meme",
        context="Aplikasi layanan publik baru diluncurkan tapi langsung server down saat pendaftaran dibuka.",
        response="Hebat bgt rekor baru: belum sempet di-download udah crash duluan. Anggarannya berapa milyar nih kira-kira?",
    ),
    ConversationSample(
        register="sarkastik",
        topic="sosial",
        intent="Emotional Outburst",
        context="Klarifikasi permintaan maaf tanpa sanksi setelah bikin kegaduhan publik.",
        response="Tinggal bikin video pasang muka melas terus bilang 'khilaf', besoknya diulangin lagi. Klasik bgt!",
    ),
]


class StyleRealizer:
    """Mesin penyusun prompt berbasis few-shot retrieval percakapan riil."""

    def __init__(self, corpus: Optional[List[ConversationSample]] = None):
        self.corpus = corpus or FEW_SHOT_CORPUS

    def retrieve_few_shots(
        self,
        register: str,
        topic: str = "kebijakan_publik",
        intent: Optional[str] = None,
        k: int = 3,
    ) -> List[ConversationSample]:
        """Ambil 3-5 contoh percakapan riil terdekat berdasarkan register dan topik."""
        exact_matches = [s for s in self.corpus if s.register == register and s.topic == topic]
        register_matches = [s for s in self.corpus if s.register == register]
        other_matches = [s for s in self.corpus if s not in register_matches]

        pool = exact_matches + [s for s in register_matches if s not in exact_matches] + other_matches

        # Prioritaskan intent jika cocok
        if intent:
            pool.sort(key=lambda s: 0 if s.intent == intent else 1)

        return pool[: max(3, min(k, 5))]

    def build_thread_prompt(
        self,
        persona: Persona,
        parent_post: str,
        thread_history: List[Dict[str, str]],
        intent: IntentType,
        topic: str = "kebijakan_publik",
    ) -> Dict[str, Any]:
        """Rakit prompt thread transcript lengkap dengan few-shot percakapan."""
        few_shots = self.retrieve_few_shots(
            register=persona.language_register,
            topic=topic,
            intent=intent.value,
            k=4,
        )

        formatted_few_shots = []
        for i, s in enumerate(few_shots, 1):
            formatted_few_shots.append(
                f"[Contoh {i} - {s.register.upper()} - {s.intent}]\n"
                f"Konteks: {s.context}\n"
                f"Respon: {s.response}"
            )

        history_lines = []
        for h in thread_history[-4:]:  # 4 pesan terakhir
            author = h.get("author", "User")
            text = h.get("text", "")
            history_lines.append(f"{author}: {text}")

        thread_context_str = "\n".join(history_lines) if history_lines else f"Post: {parent_post}"

        system_instruction = (
            f"Anda adalah akun netizen Indonesia dengan profil berikut:\n"
            f"- Usia: {persona.age_range}\n"
            f"- Domisili: {persona.domicile}\n"
            f"- Register Bahasa: {persona.language_register}\n"
            f"- Kecenderungan Emosi/Anger: {persona.baseline_anger}\n"
            f"- Penggunaan Emoji: {persona.emoji_frequency}\n"
            f"Hasilkan komentar balasan sesuai register bahasa di atas, natural tanpa penjelasan meta."
        )

        user_prompt = (
            f"Berikut beberapa contoh gaya penulisan yang natural ({persona.language_register}):\n\n"
            + "\n\n".join(formatted_few_shots)
            + f"\n\n---\n"
            f"Percakapan Saat Ini:\n"
            f"{thread_context_str}\n\n"
            f"Tujuan Interaksi (Intent): {intent.value}\n"
            f"Target Panjang: ~{int(round(2.718 ** persona.comment_length_mu))} kata.\n"
            f"Tulis komentar balasan Anda sekarang:"
        )

        return {
            "system_instruction": system_instruction,
            "user_prompt": user_prompt,
            "few_shots_used": len(few_shots),
            "persona_id": persona.persona_id,
            "intent": intent.value,
        }
