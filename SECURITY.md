# Security Policy

## Supported Versions

Kami secara aktif memelihara dan memberikan pembaruan keamanan untuk versi-versi berikut:

| Version | Supported          |
| ------- | ------------------ |
| 3.4.x   | :white_check_mark: |
| 3.3.x   | :white_check_mark: |
| 3.2.x   | :white_check_mark: |
| < 3.2   | :x:                |

## Reporting a Vulnerability

Keamanan MiroFish Enterprise adalah prioritas utama. Jika Anda menemukan kerentanan keamanan (vulnerability) atau potensi celah keamanan:

1. **JANGAN** membuat public issue atau pull request terbuka yang mengekspos detail kerentanan.
2. Silakan laporkan melalui fitur **Private Vulnerability Reporting** di GitHub tab [Security Advisories](https://github.com/biezz-2/Mirofish-enterprise/security/advisories/new) repository ini.
3. Tim keamanan akan merespons dalam waktu 48 jam dan memverifikasi laporan Anda.
4. Kami akan menyiapkan patch keamanan melalui private fork dan merilis Security Advisory CVE terkoordinasi.

## Automated Security Audits

Repository ini dilengkapi dengan automasi keamanan berkelanjutan:
- **GitHub CodeQL Analysis**: Analisis statis semantik mendalam untuk mendeteksi celah injeksi, otorisasi, dan CWE/OWASP Top 10 pada Python dan JavaScript/TypeScript.
- **GitHub Dependabot**: Pemantauan harian terhadap CVE dependensi npm, PyPI, dan GitHub Actions.
- **Pip-Audit & NPM Audit CI**: Audit otomatis setiap push dan pull request.
- **Secret Scanning & Gitleaks**: Pencegahan kebocoran kredensial dan API keys.
- **Trivy Container & FS Scanner**: Pemindaian kerentanan pada level filesystem dan konfigurasi Docker.
