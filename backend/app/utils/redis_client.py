"""
Modul Utilitas & Klien Redis Aman (Requirepass Enforcement)
Mendukung:
1. Parsing Redis URL dengan password terisi dan kosong.
2. Konstruksi Redis URL sesuai standar RFC dan Redis URI scheme.
3. Penegakan autentikasi (requirepass): menolak koneksi anonymous jika REDIS_PASSWORD diwajibkan.
4. Klien Redis tangguh yang kompatibel baik dengan native socket (RESP) maupun redis-py jika terpasang.
"""
from __future__ import annotations

import os
import socket
import urllib.parse
from typing import Optional, Dict, Any, Union


def parse_redis_url(url: str) -> Dict[str, Any]:
    """
    Mem-parsing URL Redis dan mengekstrak komponen koneksi.
    Mendukung skema redis:// dan rediss://.

    Returns dict:
        scheme: str ('redis' atau 'rediss')
        host: str
        port: int
        username: Optional[str]
        password: Optional[str]
        db: int
        has_password: bool
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL Redis harus berupa string non-kosong")

    parsed = urllib.parse.urlparse(url)
    scheme = parsed.scheme.lower() if parsed.scheme else "redis"
    if scheme not in ("redis", "rediss"):
        raise ValueError(f"Skema URL tidak didukung: {scheme}. Gunakan 'redis' atau 'rediss'.")

    host = parsed.hostname or "127.0.0.1"
    port = parsed.port if parsed.port is not None else 6379
    username = parsed.username
    password = parsed.password

    db = 0
    if parsed.path and parsed.path != "/":
        clean_path = parsed.path.lstrip("/")
        try:
            db = int(clean_path.split("?")[0])
        except ValueError:
            db = 0

    return {
        "scheme": scheme,
        "host": host,
        "port": port,
        "username": username,
        "password": password if password is not None else "",
        "db": db,
        "has_password": bool(password),
    }


def build_redis_url(
    host: str = "127.0.0.1",
    port: int = 6379,
    password: Optional[str] = None,
    db: int = 0,
    scheme: str = "redis",
) -> str:
    """
    Membangun string koneksi Redis URL yang terstandardisasi.
    Jika password diisi: redis://:{password}@{host}:{port}/{db}
    Jika password kosong: redis://{host}:{port}/{db}
    """
    clean_pwd = (password or "").strip()
    if clean_pwd:
        quoted_pwd = urllib.parse.quote(clean_pwd, safe="")
        return f"{scheme}://:{quoted_pwd}@{host}:{port}/{db}"
    return f"{scheme}://{host}:{port}/{db}"


def enforce_redis_credentials(
    url: str,
    required_password: Optional[str] = None,
) -> str:
    """
    Memvalidasi dan menegakkan kepatuhan autentikasi requirepass pada URL Redis.
    Jika required_password diset:
      - Menolak koneksi anonymous (tanpa password) dengan PermissionError.
      - Menolak jika password pada URL tidak cocok dengan required_password.
    Mengembalikan URL terverifikasi.
    """
    parsed = parse_redis_url(url)
    req_pwd = (required_password or "").strip()

    if req_pwd:
        if not parsed["has_password"] or not parsed["password"]:
            raise PermissionError(
                "Penolakan koneksi Redis: REDIS_PASSWORD diwajibkan tetapi kredensial tidak ditemukan pada URL (anonymous login dilarang)."
            )
        if parsed["password"] != req_pwd:
            raise PermissionError(
                "Penolakan koneksi Redis: Kredensial password yang diberikan tidak cocok dengan REDIS_PASSWORD yang diwajibkan."
            )

    return url


def get_hardened_redis_url(
    raw_url: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    password: Optional[str] = None,
    db: Optional[int] = None,
    required_password: Optional[str] = None,
) -> str:
    """
    Menghasilkan URL Redis yang di-harden.
    Jika raw_url disediakan:
      - Jika required_password diset namun raw_url belum berpassword,
        injeksi password tersebut atau validasi integritasnya.
    Jika raw_url tidak disediakan:
      - Dibangun menggunakan build_redis_url().
    """
    req_pwd = (required_password or "").strip()
    pwd = (password or req_pwd).strip()

    if raw_url:
        parsed = parse_redis_url(raw_url)
        if req_pwd and not parsed["has_password"]:
            # Perbarui URL dengan menyematkan password wajib
            return build_redis_url(
                host=parsed["host"],
                port=parsed["port"],
                password=req_pwd,
                db=parsed["db"],
                scheme=parsed["scheme"]
            )
        return enforce_redis_credentials(raw_url, required_password=req_pwd)

    target_host = host or "127.0.0.1"
    target_port = port or 6379
    target_db = db or 0
    return build_redis_url(host=target_host, port=target_port, password=pwd, db=target_db)


class HardenedRedisClient:
    """
    Klien Redis ter-harden untuk MiroFish Enterprise.
    Mencegah anonymous login ketika server mengharuskan requirepass.
    """

    def __init__(
        self,
        url_or_host: str = "127.0.0.1",
        port: int = 6379,
        password: Optional[str] = None,
        db: int = 0,
        required_password: Optional[str] = None,
        timeout: float = 2.0,
    ):
        self.timeout = timeout
        self.required_password = (required_password or "").strip()

        if url_or_host.startswith("redis://") or url_or_host.startswith("rediss://"):
            enforce_redis_credentials(url_or_host, required_password=self.required_password)
            parsed = parse_redis_url(url_or_host)
            self.host = parsed["host"]
            self.port = parsed["port"]
            self.password = parsed["password"]
            self.db = parsed["db"]
            self.scheme = parsed["scheme"]
        else:
            self.host = url_or_host
            self.port = port
            self.password = (password or "").strip()
            self.db = db
            self.scheme = "redis"

            if self.required_password:
                if not self.password:
                    raise PermissionError(
                        "Penolakan koneksi Redis: anonymous login ditolak karena REDIS_PASSWORD diwajibkan."
                    )
                if self.password != self.required_password:
                    raise PermissionError(
                        "Penolakan koneksi Redis: password tidak cocok dengan REDIS_PASSWORD."
                    )

    @property
    def url(self) -> str:
        return build_redis_url(
            host=self.host,
            port=self.port,
            password=self.password,
            db=self.db,
            scheme=self.scheme,
        )

    def ping(self, mock: bool = False) -> bool:
        """
        Menguji konektivitas ke Redis.
        Jika mock=True, hanya memvalidasi integritas kredensial tanpa membuka socket fisik.
        Jika mock=False, mengirimkan AUTH dan PING lewat protokol RESP.
        """
        if self.required_password and not self.password:
            raise PermissionError("Koneksi ditolak: REDIS_PASSWORD diwajibkan.")

        if mock:
            return True

        # Kirim perintah PING (dan AUTH jika ada password) melalui socket native
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout)
        try:
            s.connect((self.host, self.port))
            if self.password:
                auth_cmd = f"*2\r\n$4\r\nAUTH\r\n${len(self.password)}\r\n{self.password}\r\n"
                s.sendall(auth_cmd.encode("utf-8"))
                resp = s.recv(1024)
                if resp.startswith(b"-ERR") or resp.startswith(b"-WRONGPASS"):
                    raise PermissionError(f"Autentikasi Redis gagal: {resp.decode('utf-8', errors='ignore')}")

            s.sendall(b"*1\r\n$4\r\nPING\r\n")
            resp = s.recv(1024)
            return b"+PONG" in resp
        except (socket.error, ConnectionRefusedError, TimeoutError, OSError) as e:
            # Jika koneksi ke server fisik gagal (misal server offline), tapi bukan karena kesalahan auth
            raise ConnectionError(f"Gagal terhubung ke Redis di {self.host}:{self.port}: {e}") from e
        finally:
            s.close()
