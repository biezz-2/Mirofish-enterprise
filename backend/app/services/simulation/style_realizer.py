# backend/app/services/simulation/style_realizer.py
"""
Style Realizer: Template Prompt Thread Transcript dengan Few-Shot Retrieval
Menggantikan instruksi mentah kaku dengan 3-5 contoh percakapan riil per register dan topik
untuk menghasilkan gaya bahasa natural menyerupai netizen Indonesia (Dataset Notion Karhutla/Kabut Asap).
"""
from __future__ import annotations

import re
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
    platform: str = "all"


# ==============================================================================
# Bank Data Few-Shot Percakapan Riil (Notion Karhutla/Kabut Asap & Kebijakan Publik)
# Mencakup 4 Register: formal, kasual santai, gaul jaksel, sarkastik
# ==============================================================================
FEW_SHOT_CORPUS: List[ConversationSample] = [
    # --------------------------------------------------------------------------
    # Register 1: FORMAL (PUEBI baku, tertib, objektif, berbasis data/hukum/regulasi)
    # --------------------------------------------------------------------------
    ConversationSample(
        register="formal",
        topic="karhutla_kabut_asap",
        intent="Agree/Support",
        context="Kementerian Lingkungan Hidup menyegel 12 konsesi perkebunan sawit dan HTI yang terindikasi memiliki titik panas karhutla.",
        response="Langkah penegakan hukum melalui sanksi administratif dan pidana lingkungan ini harus dikawal hingga ke pengadilan. Asas tanggung jawab mutlak (strict liability) wajib diterapkan tanpa pandang bulu untuk memulihkan kerusakan hidrologis gambut.",
        platform="linkedin",
    ),
    ConversationSample(
        register="formal",
        topic="karhutla_kabut_asap",
        intent="Disagree/Counter",
        context="Pemerintah daerah mengimbau warga tetap tenang dan beraktivitas normal meski indeks kualitas udara (ISPU) berada pada level Berbahaya.",
        response="Imbauan tersebut sangat tidak bijak dan berisiko fatal bagi keselamatan publik. Pada level ISPU di atas 300, aktivitas luar ruangan wajib dihentikan, sekolah tatap muka harus dialihkan ke moda daring, dan posko oksigen darurat harus disiagakan di seluruh puskesmas.",
        platform="reddit",
    ),
    ConversationSample(
        register="formal",
        topic="karhutla_kabut_asap",
        intent="Clarification/Question",
        context="Operasi Teknologi Modifikasi Cuaca (TMC) hujan buatan dilaporkan terkendala ketiadaan bibit awan konvektif di atmosfer.",
        response="Apakah terdapat skema kontinjensi alternatif seperti mobilisasi water bombing armada helikopter tambahan dan pemadaman darat kanal basah untuk mencegah api merembet ke lapisan gambut dalam?",
        platform="twitter",
    ),
    ConversationSample(
        register="formal",
        topic="karhutla_kabut_asap",
        intent="Nuanced Synthesis",
        context="Perdebatan dampak ekonomi pembukaan lahan perkebunan vs kerugian ekologis dan kesehatan akibat bencana kabut asap.",
        response="Kerugian ekonomi akibat lonjakan kasus ISPA, penutupan bandara, dan penurunan produktivitas jauh melampaui efisiensi pembukaan lahan dengan cara membakar. Transformasi menuju audit kepatuhan zero-burning dan sertifikasi berkelanjutan yang diaudit independen adalah keharusan mutlak.",
        platform="linkedin",
    ),
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

    # --------------------------------------------------------------------------
    # Register 2: KASUAL SANTAI (Ragam lisan netizen medsos, slang otentik, ekspresif)
    # --------------------------------------------------------------------------
    ConversationSample(
        register="kasual santai",
        topic="karhutla_kabut_asap",
        intent="Emotional Outburst",
        context="Kabut asap pagi ini pekat sekali, jarak pandang di jalan raya kurang dari 50 meter dan bau hangus menyengat hidung.",
        response="Ya Allah beneran parah bgt ini kabut asap, baru keluar rumah bentar aja mata langsung perih tenggorokan gatal. Plis lah bagi-bagi masker N95 gratis napa buat warga!",
        platform="tiktok",
    ),
    ConversationSample(
        register="kasual santai",
        topic="karhutla_kabut_asap",
        intent="Emotional Outburst",
        context="Beredar video anak-anak sekolah dasar berjalan kaki menembus kepungan asap tebal tanpa memakai masker pelindung.",
        response="Amit-amit liat langitnya udah kuning pekat gitu woy, sesak lgi liat kmu dek jalan kaki gak pake masker. Tolong lah dinas terkait liburin dulu sekolahnya, masa nunggu anak-anak masuk RS semua!",
        platform="tiktok",
    ),
    ConversationSample(
        register="kasual santai",
        topic="karhutla_kabut_asap",
        intent="Disagree/Counter",
        context="Himbauan agar warga cukup memperbanyak minum air putih untuk menangkal partikel racun kabut asap.",
        response="Gimana ceritanya disuruh cuma banyakin minum air putih, ini paru-paru udah kayak kena saringan knalpot woy. Beneran parah bgt solusinya, gak ada empati blas sama warga yg sesak napas.",
        platform="twitter",
    ),
    ConversationSample(
        register="kasual santai",
        topic="karhutla_kabut_asap",
        intent="Agree/Support",
        context="Komunitas relawan membuka posko bantuan oksigen darurat gratis untuk lansia dan balita korban asap.",
        response="Alhamdulillah respek bgt sama temen-temen relawan! Daripada nunggu aksi pejabat yg lelet, gerakan warga gini yg bener-bener nyelametin nyawa.",
        platform="instagram",
    ),
    ConversationSample(
        register="kasual santai",
        topic="karhutla_kabut_asap",
        intent="Sarcasm/Meme",
        context="Foto jemuran baju warga berubah warna jadi abu-abu kecokelatan karena debu jelaga karhutla.",
        response="Wkwk jemur baju putih pulang-pulang dapet edisi tie-dye asap karhutla. Asli nyesek tapi mau nangis juga air mata kalah sama perihnya asap.",
        platform="twitter",
    ),
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
    ConversationSample(
        register="kasual santai",
        topic="teknologi",
        intent="Agree/Support",
        context="Inovasi model AI baru bisa jalan lancar di laptop spek pas-pasan.",
        response="Gokil sih ini, kirain bakalan berat bgt wkwk. Bener bgt sih pengembangannya ngebantu bgt buat riset lokal!",
    ),
    ConversationSample(
        register="kasual santai",
        topic="sosial",
        intent="Sarcasm/Meme",
        context="Drama antrean promo makanan murah berujung ricuh di pusat perbelanjaan.",
        response="Wkwk gokil emang warga kita kalo urusan diskon, padahal selisih goceng doang ampe senggol-bacok.",
    ),

    # --------------------------------------------------------------------------
    # Register 3: GAUL JAKSEL (Code-mixing Indo-Inggris, urban, tech/office culture)
    # --------------------------------------------------------------------------
    ConversationSample(
        register="gaul jaksel",
        topic="karhutla_kabut_asap",
        intent="Emotional Outburst",
        context="Indeks kualitas udara (AQI) di kota-kota terdampak karhutla menembus angka 420 (Kategori Hazardous).",
        response="Literally apocalyptic vibe bgt liat footage langit kuning pekat di Sumatera & Kalimantan. AQI 420 tuh udah not make sense buat manusia napas, jujurly suffocating parah ampe air purifier di kamar meraung terus.",
        platform="twitter",
    ),
    ConversationSample(
        register="gaul jaksel",
        topic="karhutla_kabut_asap",
        intent="Disagree/Counter",
        context="Asosiasi perusahaan beralasan kebakaran terjadi murni karena anomali cuaca El Nino.",
        response="Classic corporate excuse bgt blaming nature. Which is pembakaran lahan gambut tuh sengaja biar cut cost land clearing kan? Zero accountability parah, padahal public health dampaknya draining bgt!",
        platform="reddit",
    ),
    ConversationSample(
        register="gaul jaksel",
        topic="karhutla_kabut_asap",
        intent="Nuanced Synthesis",
        context="Karyawan di wilayah terdampak tetap diwajibkan masuk kantor (WFO) di tengah kondisi udara berbahaya.",
        response="Honestly speaking, mental health and respiratory safety should be top priority. Perusahaan harusnya aware and implement WFH policy secepatnya, bukan malah denial pura-pura fine-fine aja.",
        platform="linkedin",
    ),
    ConversationSample(
        register="gaul jaksel",
        topic="karhutla_kabut_asap",
        intent="Agree/Support",
        context="Komunitas anak muda menggalang donasi air purifier portabel dan masker medis untuk puskesmas daerah.",
        response="Which is good sih ya inisiatif mutual aid kayak gini. Solidaritas warga emang helpful bgt di tengah minimnya respon cepat dari birokrasi.",
        platform="instagram",
    ),
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

    # --------------------------------------------------------------------------
    # Register 4: SARKASTIK (Satir tajam, ironis, sinis, membalikkan logika retorika)
    # --------------------------------------------------------------------------
    ConversationSample(
        register="sarkastik",
        topic="karhutla_kabut_asap",
        intent="Sarcasm/Meme",
        context="Pernyataan pejabat yang menyebut kabut asap tahun ini adalah 'kiriman berkah alam' yang tidak perlu dikeluhkan.",
        response="Luar biasa solutif ya para pejabat kita, besok-besok sekalian aja kabut asapnya dijadiin destinasi wisata terapi inhalasi arang gratis biar makin berfaedah.",
        platform="twitter",
    ),
    ConversationSample(
        register="sarkastik",
        topic="karhutla_kabut_asap",
        intent="Sarcasm/Meme",
        context="Pemerintah setempat membagikan masker kain tipis selapis kepada siswa sekolah di zona merah karhutla.",
        response="Hebat bgt rekor inovasinya: masker kain selapis buat nyaring debu PM2.5. Sekalian aja dibagiin saringan santan pak, biar jelaga asapnya makin lancar masuk ke paru-paru.",
        platform="tiktok",
    ),
    ConversationSample(
        register="sarkastik",
        topic="karhutla_kabut_asap",
        intent="Disagree/Counter",
        context="Klaim titik api karhutla sudah berkurang 90% padahal citra satelit memperlihatkan ratusan hotspot baru.",
        response="Iya percaya kok titik apinya berkurang, yang bertambah cuma titik-titik makam pasien ISPA. Klasik bgt statistiknya disulap biar keliatan kerja keras!",
        platform="reddit",
    ),
    ConversationSample(
        register="sarkastik",
        topic="karhutla_kabut_asap",
        intent="Emotional Outburst",
        context="Korporasi terduga pembakar lahan gambut hanya dijatuhi sanksi teguran tertulis tanpa denda operasional.",
        response="Ditegur tertulis gaes, amit-amit jangan sampe surat tegurannya kebakar asap nanti repot bikin arsipnya lagi! Hukum kita emang setajam silet ke rakyat jelata tapi selunak agar-agar ke cukong.",
        platform="twitter",
    ),
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


# ==============================================================================
# Panduan Karakteristik Platform Medsos
# ==============================================================================
PLATFORM_STYLE_RULES: Dict[str, Dict[str, Any]] = {
    "tiktok": {
        "vibe": "Sangat santai, lisan, spontan, ekspresif, dan berorientasi video/reaksi cepat",
        "guidance": (
            "- Format TikTok: Komentar sangat santai, lisan, spontan, dan ekspresif (1-2 kalimat ringkas).\n"
            "- Gunakan ragam lisan/slang viral netizen Indonesia: 'ya Allah', 'amit-amit', 'sesak lgi liat kmu dek', 'beneran parah bgt woy', 'gak kuat bgt', 'plis lah'.\n"
            "- Tunjukkan reaksi emosional instan terhadap apa yang terlihat di video/lapangan (misal: langit oranye/kuning pekat, anak sekolah batuk-batuk, masker tipis).\n"
            "- HINDARI tulisan panjang berparagraf layaknya esai atau artikel berita."
        ),
        "example": "ya Allah beneran parah bgt kabutnya, sesak lgi liat kmu dek jalan kaki gak pake masker 😭 amit-amit jgn sampe kena ispa woy!"
    },
    "linkedin": {
        "vibe": "Sangat profesional, konstruktif, berorientasi tata kelola, ESG, dan kepatuhan industri",
        "guidance": (
            "- Format LinkedIn: Bahasa Indonesia baku yang santun, tertib, objektif, dan bernuansa profesional korporat.\n"
            "- Fokus pada aspek tata kelola lingkungan (ESG), kepatuhan audit sekat kanal lahan gambut, tanggung jawab sosial korporasi (CSR), keselamatan kerja (HSE), dan mitigasi risiko jangka panjang.\n"
            "- Sajikan rekomendasi terstruktur dan berbasis data kebijakan publik.\n"
            "- DILARANG menggunakan kata umpatan, singkatan alay berlebihan, atau sarkasme murahan."
        ),
        "example": "Krisis kabut asap ini menjadi alarm nyata perlunya audit kepatuhan ESG yang ketat pada konsesi perkebunan. Industri harus memprioritaskan mitigasi risiko lingkungan dan perlindungan kesehatan tenaga kerja secara berkelanjutan."
    },
    "reddit": {
        "vibe": "Argumentatif, analitis mendalam, skeptis terhadap retorika, dan berbasis data komunitas",
        "guidance": (
            "- Format Reddit: Diskusi mendalam, argumentatif, analitis, dan mengupas akar masalah secara sistemik.\n"
            "- Gunakan data empiris dan fakta lapangan: Indeks AQI/ISPU, koordinat titik api satelit (NASA FIRMS/BMKG), tanggung jawab hukum korporasi (strict liability), dan rekam jejak regulasi.\n"
            "- Skeptis terhadap narasi resmi pemerintah/korporasi; buka ruang debat logis multi-sudut pandang.\n"
            "- Nada kritis, blak-blakan, tidak basa-basi diplomatis."
        ),
        "example": "Masalah karhutla ini siklus tahunan yang solusinya selalu reaktif. Kalau penegakan hukum strict liability ke korporasi konsesi gak jalan dan audit kanalisasi gambut gak dibuka transparan, tahun depan AQI 400+ pasti terulang lagi."
    },
    "twitter": {
        "vibe": "Ringkas, tajam, reaktif terhadap waktu nyata (real-time updates), dan bernada lugas",
        "guidance": (
            "- Format Twitter/X: Ringkas (1-3 kalimat tajam), reaktif terhadap berita terkini, foto udara, dan keresahan publik.\n"
            "- Gunakan bahasa lisan medsos yang luwes dengan singkatan natural ('bener bgt sih', 'parah bgt', 'plis', 'asli', 'wkwk').\n"
            "- Tanggapi isu dengan nada lugas, sindiran satir cerdas, atau seruan solidaritas warga."
        ),
        "example": "Beneran parah bgt woy kabut asap hari ini, napas aja sesak dan langit udah sepia gini dibilang aman. Mau nunggu korban ISPA nambah berapa banyak lagi??"
    },
    "x": {
        "vibe": "Ringkas, tajam, reaktif terhadap waktu nyata (real-time updates), dan bernada lugas",
        "guidance": (
            "- Format Twitter/X: Ringkas (1-3 kalimat tajam), reaktif terhadap berita terkini, foto udara, dan keresahan publik.\n"
            "- Gunakan bahasa lisan medsos yang luwes dengan singkatan natural ('bener bgt sih', 'parah bgt', 'plis', 'asli', 'wkwk').\n"
            "- Tanggapi isu dengan nada lugas, sindiran satir cerdas, atau seruan solidaritas warga."
        ),
        "example": "Beneran parah bgt woy kabut asap hari ini, napas aja sesak dan langit udah sepia gini dibilang aman. Mau nunggu korban ISPA nambah berapa banyak lagi??"
    },
    "instagram": {
        "vibe": "Personal, empatik, estetis-reflektif, dan berfokus pada dampak kemanusiaan keseharian",
        "guidance": (
            "- Format Instagram: Nada empatik, personal, dan reflektif menanggapi visual situasi di lapangan.\n"
            "- Soroti dampak nyata pada keluarga, lansia, dan anak-anak yang terpaksa menghirup udara beracun.\n"
            "- Ajak kepedulian bersama dan saling menjaga kesehatan."
        ),
        "example": "Sedih bgt liat kondisi adik-adik di posko pengungsian kabut asap. Langit gelap gulita dan oksigen menipis. Stay safe semuanya, jangan lupa pakai masker medis/N95 ya."
    },
    "facebook": {
        "vibe": "Komunitas lokal, kekeluargaan, saling berbagi info posko, dan doa bersama",
        "guidance": (
            "- Format Facebook: Narasi hangat khas komunitas warga lokal, kepedulian sosial, dan doa bersama.\n"
            "- Berbagi informasi praktis: posko pembagian masker, stok tabung oksigen, dan kondisi jarak pandang jalan lintas provinsi."
        ),
        "example": "Semoga saudara-saudara kita di Riau, Jambi, dan Kalimantan selalu diberi ketabahan dan perlindungan dari bencana kabut asap ini. Untuk warga yang melintas di Jalintim harap nyalakan lampu utama karena jarak pandang sangat terbatas."
    },
    "threads": {
        "vibe": "Percakapan santai tapi beropini jelas, opini personal berbasis pengalaman harian",
        "guidance": (
            "- Format Threads: Gaya cerita mengalir santai (conversational), personal, tapi memiliki opini tegas.\n"
            "- Cocok untuk menceritakan pengalaman langsung menghirup kabut asap di rumah atau perjalanan kantor."
        ),
        "example": "Hari ke-5 kebangun dengan aroma sangit kayu kebakar di dalam kamar. Air purifier udah kerja maksimal tapi tetep aja batuk-batuk. Kondisi udara darurat kayak gini gak boleh dinormalisasi sih."
    },
    "youtube": {
        "vibe": "Ulasan analitis, edukatif, runtut, dan terstruktur layaknya komentar video investigasi",
        "guidance": (
            "- Format YouTube: Komentar berbobot, analitis, mengulas kronologi peristiwa atau membedah video investigasi.\n"
            "- Runtut dalam menyampaikan poin argumentasi dan apresiasi terhadap jurnalisme investigasi."
        ),
        "example": "Liputan investigasi yang sangat membuka mata. Penjelasan tentang bagaimana drainase gambut membuat lahan kering kerontang dan rentan terbakar membuktikan bahwa ini murni kegagalan tata kelola, bukan sekadar faktor El Nino."
    },
}


class StyleRealizer:
    """Mesin penyusun prompt berbasis few-shot retrieval percakapan riil netizen Indonesia."""

    def __init__(self, corpus: Optional[List[ConversationSample]] = None):
        self.corpus = corpus or FEW_SHOT_CORPUS

    def _normalize_topic(self, topic: str) -> str:
        """Normalisasi topik ke kategori baku untuk few-shot matching."""
        t = str(topic or "").lower().replace("-", "_").replace(" ", "_")
        if any(k in t for k in ["karhutla", "asap", "kabut", "jerebu", "kebakaran", "ispa", "gambut", "polusi", "hutan", "lingkungan", "bencana"]):
            return "karhutla_kabut_asap"
        if any(k in t for k in ["kebijakan", "regulasi", "pemerintah", "fiskal", "anggaran", "publik", "hukum"]):
            return "kebijakan_publik"
        if any(k in t for k in ["tech", "teknologi", "ai", "gadget", "software", "laptop", "aplikasi"]):
            return "teknologi"
        if any(k in t for k in ["ekonomi", "pasar", "bisnis", "inflasi", "harga", "subsidi", "umkm", "pajak"]):
            return "ekonomi"
        if any(k in t for k in ["karir", "karier", "kerja", "kantor", "wfh", "wfo", "hustle"]):
            return "karier"
        if any(k in t for k in ["sosial", "masyarakat", "warga", "promo", "pungli", "parkir"]):
            return "sosial"
        return t

    def retrieve_few_shots(
        self,
        register: str,
        topic: str = "kebijakan_publik",
        intent: Optional[str] = None,
        k: int = 3,
        platform: Optional[str] = None,
    ) -> List[ConversationSample]:
        """
        Ambil 3-5 contoh percakapan riil terdekat berdasarkan register, topik, platform, dan intent.
        Prioritas:
        1. Exact match (register + normalized topic + platform matching)
        2. Exact match (register + normalized topic)
        3. Register matches
        4. Topic matches dari register lain
        5. General pool
        """
        norm_topic = self._normalize_topic(topic)
        plat_lower = (platform or "all").lower()

        exact_topic_matches = [
            s for s in self.corpus
            if s.register == register and (s.topic == topic or self._normalize_topic(s.topic) == norm_topic)
        ]

        # Prioritaskan kecocokan platform jika tersedia
        platform_matched = [s for s in exact_topic_matches if s.platform in (plat_lower, "all")]
        exact_pool = platform_matched if platform_matched else exact_topic_matches

        register_matches = [s for s in self.corpus if s.register == register and s not in exact_pool]
        topic_matches = [
            s for s in self.corpus
            if (s.topic == topic or self._normalize_topic(s.topic) == norm_topic)
            and s not in exact_pool
            and s not in register_matches
        ]
        other_matches = [
            s for s in self.corpus
            if s not in exact_pool and s not in register_matches and s not in topic_matches
        ]

        pool = exact_pool + register_matches + topic_matches + other_matches

        # Prioritaskan intent jika diminta
        if intent:
            pool.sort(key=lambda s: 0 if s.intent.lower() == str(intent).lower() else 1)

        return pool[: max(3, min(k, 5))]

    def build_thread_prompt(
        self,
        persona: Persona,
        parent_post: str,
        thread_history: List[Dict[str, str]],
        intent: IntentType,
        topic: str = "kebijakan_publik",
        platform: str = "twitter",
    ) -> Dict[str, Any]:
        """Rakit prompt thread transcript lengkap dengan few-shot percakapan otentik."""
        few_shots = self.retrieve_few_shots(
            register=persona.language_register,
            topic=topic,
            intent=intent.value,
            k=4,
            platform=platform,
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
            f"- Platform: {platform.upper()}\n"
            f"Hasilkan komentar balasan sesuai register bahasa di atas, natural tanpa penjelasan meta."
        )

        user_prompt = (
            f"Berikut beberapa contoh gaya penulisan yang natural ({persona.language_register}):\n\n"
            + "\n\n".join(formatted_few_shots)
            + f"\n\n---\n"
            f"Percakapan Saat Ini ({platform.upper()}):\n"
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

    def determine_register(self, profile_data: Any) -> str:
        """Deteksi register bahasa berdasarkan data profil persona / user_info."""
        if hasattr(profile_data, "language_register") and profile_data.language_register:
            return profile_data.language_register

        text_to_check = ""
        if isinstance(profile_data, dict):
            if "language_register" in profile_data:
                return profile_data["language_register"]
            other_info = profile_data.get("other_info", {})
            text_to_check = " ".join([
                str(profile_data.get("description", "")),
                str(profile_data.get("user_profile", "")),
                str(profile_data.get("bio", "")),
                str(profile_data.get("persona", "")),
                str(other_info.get("user_profile", "")),
                str(other_info.get("mbti", "")),
            ]).lower()
        elif hasattr(profile_data, "description") or hasattr(profile_data, "profile") or hasattr(profile_data, "personality"):
            desc = getattr(profile_data, "description", "") or ""
            personality = getattr(profile_data, "personality", "") or ""
            traits = getattr(profile_data, "traits", []) or []
            traits_str = " ".join(traits) if isinstance(traits, list) else str(traits)
            prof = getattr(profile_data, "profile", {}) or {}
            other_info = prof.get("other_info", {}) if isinstance(prof, dict) else {}
            user_prof = other_info.get("user_profile", "") if isinstance(other_info, dict) else ""
            text_to_check = f"{desc} {personality} {traits_str} {user_prof}".lower()
        elif isinstance(profile_data, str):
            text_to_check = profile_data.lower()

        if any(w in text_to_check for w in ["sarkas", "nyindir", "skeptis", "satir", "cynical", "sinis", "oposisi"]):
            return "sarkastik"
        if any(w in text_to_check for w in ["jaksel", "scbd", "startup", "creative", "gen z", "millennial", "agency", "tech bro"]):
            return "gaul jaksel"
        if any(w in text_to_check for w in ["dosen", "akademisi", "pejabat", "pemerintah", "resmi", "peneliti", "profesional", "formal", "menteri", "pakar"]):
            return "formal"
        if any(w in text_to_check for w in ["kritis"]):
            return "sarkastik"
        return "kasual santai"

    def format_style_guidance(
        self,
        register: str,
        topic: str = "kebijakan_publik",
        few_shots: Optional[List[ConversationSample]] = None,
        platform: str = "twitter",
    ) -> str:
        """Format panduan gaya bahasa netizen Indonesia dan few-shot examples."""
        samples = few_shots or self.retrieve_few_shots(register=register, topic=topic, k=3, platform=platform)

        sample_blocks = []
        for i, s in enumerate(samples, 1):
            sample_blocks.append(
                f"[Contoh {i} - {s.register.upper()}]\n"
                f"Konteks: {s.context}\n"
                f"Komentar Otentik: \"{s.response}\""
            )
        few_shot_text = "\n\n".join(sample_blocks)

        register_notes = {
            "formal": (
                "- Gunakan bahasa Indonesia baku PUEBI yang santun, tertib, dan objektif.\n"
                "- Tunjukkan argumen berbobot, berbasis fakta, data, atau logika rasional hukum/kebijakan."
            ),
            "kasual santai": (
                "- Gunakan bahasa percakapan sehari-hari netizen Indonesia.\n"
                "- Gunakan kata-kata otentik lisan medsos: 'ya Allah', 'amit-amit', 'sesak lgi liat kmu dek', 'beneran parah bgt', 'bener bgt sih', 'wkwk', 'gokil', 'parah', 'banget/bgt', 'gak/nggak', 'udah/udh', 'beneran', 'plis lah'.\n"
                "- Spontan, luwes, ekspresif, dan tidak kaku."
            ),
            "gaul jaksel": (
                "- Gunakan code-mixing bahasa Indonesia - Inggris gaya anak muda urban/Jaksel.\n"
                "- Contoh ungkapan otentik: 'literally', 'jujurly', 'which is', 'basically', 'prefer', 'draining', 'fine-fine aja', 'gokil sih', 'apocalyptic vibe', 'not make sense', 'suffocating'.\n"
                "- Selipkan ekspresi tren perkotaan kontemporer dan refleksi realitas sosial."
            ),
            "sarkastik": (
                "- Gunakan nada satir, ironis, atau sindiran tajam khas netizen medsos Indonesia.\n"
                "- Contoh ungkapan otentik: 'Iya percaya kok', 'luar biasa solutif ya', 'hebat bgt', 'klasik bgt', 'wkwk gokil', 'selamat menikmati', 'saringan santan', 'nunggu insang tumbuh'.\n"
                "- Tanggapi isu dengan nada sinis, lelucon bernuansa getir, atau membalikkan logika retorika pejabat."
            ),
        }
        notes = register_notes.get(register, register_notes["kasual santai"])

        # Panduan karakteristik platform
        plat_key = platform.lower()
        plat_cfg = PLATFORM_STYLE_RULES.get(plat_key, PLATFORM_STYLE_RULES["twitter"])
        plat_guidance = plat_cfg["guidance"]

        return (
            f"\n\n# ATURAN GAYA KOMUNIKASI & REGISTER BAHASA NETIZEN INDONESIA ({platform.upper()})\n"
            f"Anda adalah akun netizen Indonesia nyata di {platform}. Berkomentarlah secara otentik!\n"
            f"Register Anda: **{register.upper()}**\n\n"
            f"Panduan Register:\n{notes}\n\n"
            f"Panduan Karakteristik Platform ({platform.upper()}):\n{plat_guidance}\n\n"
            f"Kaidah Wajib (Anti-Bot & Anti-Meta):\n"
            f"1. DILARANG KERAS menggunakan frasa meta AI seperti 'Sebagai AI...', 'Sebagai model bahasa...', atau klarifikasi robotik.\n"
            f"2. Bersikaplah 100% sebagai manusia nyata pemilik akun dengan kepribadian dan opini subjektif.\n"
            f"3. Jangan membuat tulisan seperti artikel esai panjang jika hanya merespons atau berkomentar pendek.\n\n"
            f"Contoh Komentar Riil Netizen Indonesia ({register}):\n"
            f"{few_shot_text}\n"
        )

    def build_natural_system_prompt(
        self,
        base_prompt: str,
        user_info: Any = None,
        register: Optional[str] = None,
        platform: str = "twitter",
        topic: str = "kebijakan_publik",
    ) -> str:
        """Suntikkan aturan gaya bahasa natural netizen Indonesia ke system message OASIS."""
        reg = register or self.determine_register(user_info)
        context_str = f"{base_prompt} {str(user_info)}".lower()
        if any(w in context_str for w in ["karhutla", "asap", "kabut", "jerebu", "kebakaran", "ispa", "gambut", "polusi", "hutan"]):
            effective_topic = "karhutla_kabut_asap"
        else:
            effective_topic = topic
        guidance = self.format_style_guidance(register=reg, topic=effective_topic, platform=platform)
        return f"{base_prompt.rstrip()}\n{guidance}\n"


# Singleton instance
style_realizer = StyleRealizer()
