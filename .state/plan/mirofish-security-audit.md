# Rencana Komprehensif: Full Scope Security Audit & Targeted Patching MiroFish (5 Sesi Jules)

## 1. Executive Summary & Objective
MiroFish Enterprise merupakan platform multi-komponen yang mencakup backend Python/Flask, frontend Vue 3, database, integrasi LLM/OASIS simulation, serta konfigurasi deployment (Docker, ecosystem PM2). Rencana kerja audit dan remediasi keamanan dibagi menjadi **5 sesi mandiri untuk Google Jules Coding Agent** agar eksekusi dapat berjalan paralel, terfokus, terisolasi, dan menghasilkan Pull Request (PR) modular yang mudah ditinjau.

---

## 2. Pemetaan 5 Sesi Jules

### Sesi 1: Dependency Security Audit & Package Hardening
- **Target**: `backend/requirements.txt`, `backend/pyproject.toml`, `backend/uv.lock`, `package.json`, `package-lock.json`.
- **Fokus**: Audit paket dependensi backend (Python) dan frontend (Node.js) terhadap CVE aktif, mengupgrade ke versi patch aman (non-breaking), dan membersihkan dependensi usang.
- **Verifikasi**: `pytest` lolos untuk backend, `npm run build` sukses untuk frontend.

### Sesi 2: Backend API Authentication, Authorization & Route Protection
- **Target**: `backend/app/routes/` (`auth.py`, `project.py`, `task.py`, `graph.py`, `simulation.py`, `oasis.py`, dsb).
- **Fokus**: Menerapkan decorator autentikasi dan otorisasi yang konsisten, pencegahan IDOR (Insecure Direct Object Reference) pada akses `project_id`/`task_id`/`simulation_id`, dan perlindungan endpoint administratif.
- **Verifikasi**: Unit test validasi otorisasi, penolakan request tanpa hak akses (HTTP 401/403).

### Sesi 3: Input Validation, Path Traversal Mitigation & File Upload Hardening
- **Target**: `backend/app/routes/` dan utility file upload (`backend/app/utils/`, handler di `uploads/`).
- **Fokus**: Sanitasi nama file dan canonical path check (`werkzeug.utils.secure_filename`, pencegahan path traversal `../`), validasi skema payload JSON, pembatasan MIME type & ukuran file upload, serta sanitasi query DB.
- **Verifikasi**: Unit test path traversal test cases dan payload injection rejection.

### Sesi 4: Infrastructure & Environment Hardening (Docker, PM2, Secrets & Headers)
- **Target**: `Dockerfile`, `docker-compose.yml`, `ecosystem.config.js`, `.dockerignore`, `.env.example`, `backend/app/config.py`.
- **Fokus**: Pengamanan container Docker (eksekusi non-root `appuser`), konfigurasi secure HTTP response headers (CSP, HSTS, X-Content-Type-Options, X-Frame-Options), konfigurasi CORS terisolasi, dan audit isolasi kredensial environment.
- **Verifikasi**: Docker build valid, linting konfigurasi sukses, header response terkonfigurasi.

### Sesi 5: Frontend Security Hardening & Konsolidasi SECURITY_AUDIT_REPORT.md
- **Target**: `frontend/src/` (views & components) dan dokumen `SECURITY_AUDIT_REPORT.md` di root repositori.
- **Fokus**: Audit template Vue 3 terhadap raw HTML injection / DOM XSS (`v-html`), pengamanan penyimpanan token di client, serta penyusunan dokumen laporan audit lengkap dalam Bahasa Indonesia dengan klasifikasi Critical, High, Medium, Low.
- **Verifikasi**: `npm run build` sukses, file `SECURITY_AUDIT_REPORT.md` lengkap dan komprehensif di root.

---

## 3. Detail Prompt untuk 5 Sesi Jules
Tiap prompt disusun dengan pendekatan secure engineering dan defensive coding agar tidak memicu false-positive filter Jules:

### Jules #1:
- **Title**: `Security Hardening: Dependency Audit & CVE Patching (Python & Node.js)`
- **Prompt**:
```text
Lakukan audit dan hardening dependensi pada proyek MiroFish Enterprise (biezz-2/Mirofish-enterprise):
1. Periksa dependensi backend pada backend/requirements.txt dan backend/pyproject.toml terhadap paket-paket usang atau rentan CVE yang diketahui. Perbarui ke versi patch aman tanpa merusak API compatibility.
2. Periksa dependensi frontend pada package.json dan package-lock.json terhadap advisori keamanan yang diketahui, lalu terapkan perbaikan versi aman yang kompatibel.
3. Jalankan verifikasi pengujian:
   - Backend: jalankan pengujian di folder backend menggunakan pytest untuk memastikan semua test lulus.
   - Frontend: jalankan 'npm run build' di folder frontend untuk memastikan build berhasil tanpa error.
4. Buat commit yang jelas dan ajukan Pull Request.
```

### Jules #2:
- **Title**: `Security Hardening: API Authentication, Authorization & IDOR Protection`
- **Prompt**:
```text
Tingkatkan kontrol akses, autentikasi, dan otorisasi pada seluruh route API backend MiroFish Enterprise (backend/app/routes/):
1. Audit route endpoints di backend/app/routes/ (khususnya project.py, task.py, graph.py, simulation.py, oasis.py, dan file manajemen).
2. Terapkan decorator autentikasi dan validasi otorisasi yang konsisten sehingga setiap endpoint API yang mengelola data sensitif memvalidasi hak akses pemanggil.
3. Cegah Insecure Direct Object References (IDOR) dengan memastikan bahwa akses terhadap project_id, task_id, atau simulation_id memvalidasi kepemilikan/izin resource sebelum membaca atau memodifikasi data.
4. Pastikan request yang tidak memiliki kredensial valid menghasilkan response HTTP 401/403 yang seragam tanpa mengekspos internal stack trace.
5. Tambahkan unit test untuk memverifikasi penolakan akses tidak berizin dan pastikan pytest lulus.
6. Buat commit yang jelas dan ajukan Pull Request.
```

### Jules #3:
- **Title**: `Security Hardening: Input Validation, File Upload & Path Traversal Prevention`
- **Prompt**:
```text
Terapkan validasi input yang ketat dan pertahanan terhadap Path Traversal pada sistem file upload backend MiroFish Enterprise:
1. Audit penanganan file upload dan path resolution pada backend/app/routes/ dan direktori uploads/.
2. Gunakan sanitasi nama file yang aman (misalnya werkzeug.utils.secure_filename) dan lakukan canonical path validation (os.path.realpath / Path.resolve()) untuk memastikan tidak ada input yang dapat melakukan directory traversal ('../') ke luar direktori yang diizinkan.
3. Terapkan pembatasan ukuran file maksimal (max content length) dan validasi ekstensi/MIME type file yang diperbolehkan untuk diunggah.
4. Validasi skema input payload JSON pada endpoint API untuk mencegah data tak terduga atau tipe parameter yang salah.
5. Tambahkan unit test untuk menguji percobaan path traversal dan payload abnormal, lalu pastikan pytest lulus.
6. Buat commit yang jelas dan ajukan Pull Request.
```

### Jules #4:
- **Title**: `Security Hardening: Infrastructure, Docker Non-Root, CORS & Security Headers`
- **Prompt**:
```text
Lakukan hardening konfigurasi infrastruktur, container runtime, dan security headers pada proyek MiroFish Enterprise:
1. Hardening Dockerfile: Konfigurasi container agar berjalan menggunakan non-root user (appuser/appgroup), bukan user root. Optimalkan layer caching dan pastikan file sensitif dikecualikan melalui .dockerignore.
2. Review docker-compose.yml dan ecosystem.config.js: Pastikan konfigurasi environment aman, tidak ada credentials hardcoded, dan port ekspos dibatasi dengan tepat.
3. Konfigurasi Security Headers pada aplikasi Flask backend (misalnya X-Content-Type-Options: nosniff, X-Frame-Options: DENY/SAMEORIGIN, Content-Security-Policy dasar, Referrer-Policy).
4. Perketat konfigurasi CORS (Cross-Origin Resource Sharing) agar hanya mengizinkan origin tepercaya sesuai konfigurasi environment, bukan wildcard (*).
5. Pastikan aplikasi dapat berjalan normal dengan konfigurasi baru dan buat Pull Request.
```

### Jules #5:
- **Title**: `Security Hardening: Frontend XSS Prevention & SECURITY_AUDIT_REPORT.md Synthesis`
- **Prompt**:
```text
Lakukan pengamanan frontend Vue 3 dan susun laporan audit komprehensif pada repositori MiroFish Enterprise:
1. Audit seluruh komponen dan views Vue 3 di frontend/src/ untuk memastikan tidak ada penggunaan v-html yang tidak disanitasi yang berpotensi memicu Cross-Site Scripting (DOM XSS). Pastikan penanganan token di client state aman.
2. Pastikan build frontend berhasil dengan 'npm run build' tanpa error.
3. Susun dokumen SECURITY_AUDIT_REPORT.md di root repository dalam Bahasa Indonesia yang mencakup:
   - Ringkasan Eksekutif & Postur Keamanan Sistem.
   - Ruang Lingkup Audit (Backend Python/Flask, Frontend Vue 3, Konfigurasi Docker, Dependensi Paket, API Endpoints, Secrets Scanning).
   - Klasifikasi Temuan Keamanan (Critical, High, Medium, Low) dengan rincian: ID temuan, tingkat keparahan, file/baris terkait, dampak, dan status mitigasi.
   - Rekomendasi perbaikan untuk temuan Medium dan Low.
   - Panduan Praktik Terbaik Secure Coding untuk pengembangan selanjutnya.
4. Buat commit yang rapi dan ajukan Pull Request.
```
