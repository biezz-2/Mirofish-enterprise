# Panduan Etika Penggunaan & Batasan Legal
## MiroFish Enterprise - Autonomous Multi-Agent Social Simulation Platform

---

## 1. Tujuan & Filosofi Penggunaan

**MiroFish Enterprise** dirancang secara khusus untuk pemodelan ilmiah, analisis dinamika wacana publik makro, mitigasi krisis komunikasi, dan pengujian ketahanan informasi institusional melalui simulasi multi-agen berskala besar.

Platform ini memanfaatkan teknologi graf pengetahuan (GraphRAG), metasearch privat tanpa pelacakan (SearXNG), dan persona agen otonom (model psikometri OCEAN) untuk memetakan bagaimana narasi berkembang secara statistik dalam masyarakat digital majemuk.

Penggunaan MiroFish Enterprise wajib berakar pada prinsip kehati-hatian, tanggung jawab etis, transparansi, serta penghormatan penuh terhadap hak asasi manusia dan hukum yang berlaku di yurisdiksi Republik Indonesia dan hukum internasional.

---

## 2. Batasan Legal & Landasan Regulasi

Setiap pengguna, operator, dan pengembang yang mengoperasikan MiroFish Enterprise terikat pada ketentuan hukum berikut:

1. **Undang-Undang No. 27 Tahun 2022 tentang Pelindungan Data Pribadi (UU PDP)**:
   - Dilarang mengumpulkan, memproses, atau memperjualbelikan data pribadi tanpa dasar hukum yang sah.
   - Kewajiban menerapkan prinsip minimisasi data (*data minimization*) dan pelindungan data sejak perancangan (*privacy by design*).
2. **Undang-Undang No. 1 Tahun 2024 tentang Perubahan Kedua atas UU No. 11 Tahun 2008 tentang Informasi dan Transaksi Elektronik (UU ITE)**:
   - Larangan mendistribusikan konten ilegal, pencemaran nama baik, pemerasan, ujaran kebencian, dan manipulasi data elektronik.
3. **Kitab Undang-Undang Hukum Pidana (KUHP)**:
   - Larangan penyebaran berita bohong yang menerbitkan keonaran dan tindak pidana terhadap ketertiban umum.

---

## 3. Pelarangan Keras Penggunaan (Strictly Prohibited Use Cases)

MiroFish Enterprise menerapkan kebijakan **Nol Toleransi (*Zero Tolerance*)** terhadap penyalahgunaan platform. Pelanggaran terhadap daftar larangan di bawah ini akan memicu pemutusan akses seketika, pemusnahan data proyek terkait, dan pelaporan kepada pihak berwenang jika terdapat indikasi tindak pidana.

### 3.1 Pelarangan Profiling Target Individu Nyata (Anti-Targeted Profiling)
- **Dilarang keras** memodelkan, melacak, memetakan, atau membangun persona simulasi yang meniru atau menargetkan **orang perseorangan nyata secara spesifik**, baik tokoh publik, pejabat negara, maupun warga sipil.
- Persona dalam MiroFish adalah **konstruk sintetis abstrak** berbasis arketipe demografi statistik (misal: "Segmentasi Konsumen Urban Usia 25-34"), bukan representasi digital kembar (*digital twin*) dari individu bernyawa.

### 3.2 Pelarangan Doxxing & Pelecehan Terarah (Anti-Doxxing & Anti-Harassment)
- **Dilarang keras** menyematkan kueri pencarian, unggahan teks, atau benih graf yang bertujuan mengungkap atau mengumpulkan data pribadi individu nyata, termasuk:
  - Nomor Induk Kependudukan (NIK), paspor, atau nomor identitas resmi.
  - Alamat rumah tinggal, koordinat geolokasi personal, atau rute perjalanan.
  - Nomor telepon pribadi, akun perpesanan instan, atau alamat email pribadi.
  - Nomor rekening perbankan, riwayat transaksi finansial, atau nomor kartu kredit.
  - Rekam medis, riwayat kesehatan mental, atau orientasi pribadi.
- Sistem secara otomatis mengamputasi data tersebut di tingkat gerbang masukan melalui modul `PIIScrubber`.

### 3.3 Pelarangan Disinformasi Terkoordinasi & Astroturfing
- **Dilarang keras** menggunakan luaran simulasi untuk:
  - Merancang, memproduksi, atau mengorkestrasi operasi informasi palsu (*disinformation campaign*) di dunia nyata.
  - Mengembangkan botnet atau akun klon sintetis untuk manipulasi opini (*astroturfing*) di media sosial nyata (Twitter/X, TikTok, Instagram, Facebook, Reddit, Threads).
  - Melakukan penipuan sosial (*social engineering*), impersonasi institusi keuangan, atau penipuan siber (*phishing*).

### 3.4 Pelarangan Manipulasi Pasar Modal & Keuangan
- **Dilarang keras** memanfaatkan hasil simulasi dinamika opini untuk rekayasa pasar saham, komoditas, atau aset kripto (*market manipulation / pump-and-dump*).

### 3.5 Pelarangan Hasutan SARA & Konflik Horisontal
- **Dilarang keras** menyimulasikan atau mengekstraksi narasi yang dirancang untuk memicu kekerasan fisik, diskriminasi berbasis Suku, Agama, Ras, dan Antargolongan (SARA), terorisme, atau perpecahan kedaulatan negara.

---

## 4. Kewajiban Pelabelan Konten Sintetis (Mandatory Synthetic Content Labeling)

Untuk mencegah misinterpretasi publik dan menjaga transparansi digital, setiap materi teks, laporan analitik, atau cuplikan dialog agen yang dihasilkan oleh MiroFish Enterprise **WAJIB** mematuhi protokol pelabelan berikut:

### 4.1 Watermark & Banner Sanggahan Wajib
Setiap ekspor laporan simulasi (format PDF, Markdown, HTML, atau JSON) harus memuat banner sanggahan eksplisit pada bagian pembuka:

```markdown
> ⚠️ **PERINGATAN SANGGAHAN KONTEN SINTETIS**:
> Seluruh konten, interaksi agen, sentimen, dan persona dalam dokumen ini adalah HASIL SIMULASI KOMPUTASI MULTI-AGEN AI BERDASARKAN PROBABILITAS STATISTIK.
> Konten ini BUKAN data empiris perilaku orang perseorangan nyata dan DILARANG digunakan sebagai dasar tuduhan hukum, tindakan doxxing, atau klaim faktual personal.
```

### 4.2 Pelabelan Entitas Agen Sintetis
- Seluruh agen simulasi wajib memiliki identifikasi sintetis yang jelas dalam metadata:
  ```json
  {
    "agent_id": "sim_agent_x7b8",
    "nature": "SYNTHETIC_AUTONOMOUS_PERSONA",
    "real_human_equivalent": false,
    "synthetic_disclaimer": "Generated by MiroFish Simulation Engine"
  }
  ```

### 4.3 Penyebaran ke Pihak Ketiga
- Pengguna yang mempublikasikan sebagian atau seluruh temuan riset MiroFish ke ruang publik atau media massa wajib menyertakan metodologi simulasi secara jujur dan tidak boleh menyamarkan narasi sintetis seolah-olah merupakan kutipan langsung dari tokoh atau masyarakat nyata.

---

## 5. Arsitektur Pelindung Teknis (Technical Safeguards)

MiroFish Enterprise menerapkan mekanisme pertahanan berlapis untuk menjamin etika penggunaan ditegakkan secara teknis di dalam kode (*defense-in-depth*):

1. **Modul Sanitasi PII Otomatis (`backend/app/services/pii_scrubber.py`)**:
   - Memindai dan menyamarkan NIK, nomor telepon, alamat email, rekening bank, dan nama orang secara instan pada masukan Langkah 0 (SearXNG) dan Langkah 1 (Graph Seed Ingestion).
2. **Perisai Anti-Injeksi CaMeL 3-Lapis (`backend/app/services/anti_injection.py`)**:
   - **Layer 1**: Sanitasi ekspresi reguler terhadap pola jailbreak, bypass instruksi, dan karakter tersembunyi.
   - **Layer 2**: XML Spotlighting isolasi data eksternal untuk mencegah kebocoran konteks sistem.
   - **Layer 3**: Passive Capability Gate yang mengunci eksekusi aksi berisiko tinggi.
3. **Penyaring Kredibilitas Sumber ($S_{domain} \ge 0.70$)**:
   - Menolak informasi dari domain yang tidak terverifikasi atau dikenal sebagai penyebar hoax dan disinformasi.
4. **Audit Trail Kekal (*Immutable Session Logging*)**:
   - Setiap interaksi kueri, pembentukan graf, dan jalannya simulasi dicatat dengan stempel waktu UTC tanpa menyimpan konten sensitif.

---

## 6. Sanksi atas Pelanggaran

Pelanggaran terhadap panduan etika ini dapat dikenakan tindakan administratif dan teknis berupa:
1. **Peringatan Resmi & Penghentian Sesi**: Sistem secara otomatis menghentikan simulasi jika terdeteksi kueri bermuatan pelanggaran berat.
2. **Pencabutan Kunci Akses (API Key Revocation)**: Penonaktifan izin akses organisasi atau pengguna bersangkutan secara permanen.
3. **Penghapusan Data Penuh**: Pemusnahan seluruh graf pengetahuan, embedding, dan laporan yang terkait dengan aktivitas ilegal.
4. **Eskalasi Hukum**: Penyerahan bukti audit log kepada aparat penegak hukum yang berwenang atas dugaan tindak pidana ITE atau pelanggaran UU PDP.

---

## 7. Komitmen Pengembang

Tim pengembang dan kontributor MiroFish Enterprise berkomitmen membangun teknologi kecerdasan buatan yang berkeadilan, aman, dan memajukan peradaban digital Indonesia tanpa mengorbankan privasi dan kehormatan martabat manusia.
