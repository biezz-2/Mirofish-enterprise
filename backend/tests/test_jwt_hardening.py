"""
Unit test untuk Hardening Autentikasi JWT (P1-4).
Memverifikasi:
1. Token valid berhasil didekode dengan klaim user.
2. Token tanpa tanda tangan atau tanda tangan salah menghasilkan 401 ("Invalid token signature").
3. Token kedaluwarsa (exp di masa lalu) menghasilkan 401 ("Token has expired").
4. Token dengan manipulasi algoritma ("none", "HS384", "RS256") ditolak 401.
5. Token malformed menghasilkan 401 ("Invalid token format").
6. Penegakan AUTH_REQUIRED memblokir rute terproteksi tanpa token valid.
7. Validasi klaim issuer (iss) dan audience (aud) saat dikonfigurasi.
8. Fungsi helper decode_token dan create_token.
"""

import time
import pytest
import jwt
from flask import Flask, jsonify, g
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.auth import (
    require_auth,
    decode_token,
    create_token,
    ALLOWED_JWT_ALGORITHMS,
    get_unauthorized_response,
)

TEST_SECRET = "mirofish-test-secure-key-32chars-long!"
ALT_SECRET = "another-unrelated-key-for-testing-32b"


@pytest.fixture
def auth_app():
    """Membuat aplikasi Flask pengujian dengan AUTH_REQUIRED = True"""
    app = Flask(__name__)
    app.testing = True
    app.config['SECRET_KEY'] = TEST_SECRET
    app.config['JWT_SECRET_KEY'] = TEST_SECRET
    app.config['AUTH_REQUIRED'] = True

    @app.route('/api/protected', methods=['GET'])
    @require_auth
    def protected():
        return jsonify({
            "success": True,
            "user": getattr(g, 'user', None)
        })

    return app


@pytest.fixture
def client(auth_app):
    return auth_app.test_client()


# ==============================================================================
# 1. Tes Token Valid Berhasil Didekode
# ==============================================================================

def test_valid_jwt_token_decodes_successfully(client, auth_app):
    """Token valid dengan HS256 dan exp masa depan berhasil didekode dan mengembalikan 200."""
    with auth_app.app_context():
        token = create_token(
            payload={"user_id": "usr_alpha_01", "roles": ["admin"]},
            secret_key=TEST_SECRET,
            expires_in=3600
        )

    response = client.get('/api/protected', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["user"]["id"] == "usr_alpha_01"
    assert "admin" in data["user"]["roles"]


def test_valid_jwt_token_with_sub_claim(client, auth_app):
    """Token valid dengan klaim standard 'sub' berhasil memetakan user id."""
    with auth_app.app_context():
        token = create_token(
            payload={"sub": "usr_subject_99", "roles": ["user"]},
            secret_key=TEST_SECRET,
            expires_in=1800
        )

    response = client.get('/api/protected', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["user"]["id"] == "usr_subject_99"


# ==============================================================================
# 2. Tes Token Tanpa Tanda Tangan / Tanda Tangan Salah Menghasilkan 401
# ==============================================================================

def test_token_with_wrong_signature_returns_401(client, auth_app):
    """Token yang ditandatangani dengan secret key lain wajib ditolak dengan 401 Invalid token signature."""
    with auth_app.app_context():
        tampered_token = create_token(
            payload={"user_id": "attacker", "roles": ["admin"]},
            secret_key=ALT_SECRET,
            expires_in=3600
        )

    response = client.get('/api/protected', headers={'Authorization': f'Bearer {tampered_token}'})
    assert response.status_code == 401
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert data["error"]["message"] == "Invalid token signature"


def test_token_stripped_signature_returns_401(client, auth_app):
    """Token dengan signature dihilangkan (header.payload.) wajib ditolak dengan 401."""
    with auth_app.app_context():
        valid_token = create_token(
            payload={"user_id": "usr_01"},
            secret_key=TEST_SECRET,
            expires_in=3600
        )
    parts = valid_token.split('.')
    unsigned_token = f"{parts[0]}.{parts[1]}."

    response = client.get('/api/protected', headers={'Authorization': f'Bearer {unsigned_token}'})
    assert response.status_code == 401
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert data["error"]["message"] == "Invalid token signature"


def test_token_missing_signature_segment_returns_401(client, auth_app):
    """Token yang hanya terdiri dari dua segmen (header.payload) wajib ditolak dengan 401 Invalid token format."""
    with auth_app.app_context():
        valid_token = create_token(
            payload={"user_id": "usr_01"},
            secret_key=TEST_SECRET,
            expires_in=3600
        )
    parts = valid_token.split('.')
    two_part_token = f"{parts[0]}.{parts[1]}"

    response = client.get('/api/protected', headers={'Authorization': f'Bearer {two_part_token}'})
    assert response.status_code == 401
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert data["error"]["message"] == "Invalid token format"


# ==============================================================================
# 3. Tes Token Kedaluwarsa (exp di masa lalu) Menghasilkan 401
# ==============================================================================

def test_expired_jwt_token_returns_401(client, auth_app):
    """Token dengan exp di masa lalu wajib ditolak dengan pesan 'Token has expired'."""
    now = int(time.time())
    expired_payload = {
        "user_id": "usr_expired",
        "iat": now - 7200,
        "exp": now - 3600  # Kedaluwarsa 1 jam yang lalu
    }
    expired_token = jwt.encode(expired_payload, TEST_SECRET, algorithm="HS256")

    response = client.get('/api/protected', headers={'Authorization': f'Bearer {expired_token}'})
    assert response.status_code == 401
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert data["error"]["message"] == "Token has expired"


# ==============================================================================
# 4. Tes Token dengan Algoritma yang Dimanipulasi Ditolak
# ==============================================================================

def test_manipulated_algorithm_none_rejected(client, auth_app):
    """Token yang menggunakan algoritma 'none' wajib ditolak dengan 401."""
    none_payload = {
        "user_id": "usr_evil",
        "exp": int(time.time()) + 3600
    }
    # PyJWT allow algorithm='none' only with empty key
    token_none = jwt.encode(none_payload, key="", algorithm="none")

    response = client.get('/api/protected', headers={'Authorization': f'Bearer {token_none}'})
    assert response.status_code == 401
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert data["error"]["message"] == "Invalid token algorithm"


def test_disallowed_algorithm_hs384_rejected(client, auth_app):
    """Token dengan algoritma selain HS256 (misal HS384/HS512) wajib ditolak karena pinning HS256."""
    payload = {
        "user_id": "usr_hs384",
        "exp": int(time.time()) + 3600
    }
    token_hs384 = jwt.encode(payload, TEST_SECRET, algorithm="HS384")

    response = client.get('/api/protected', headers={'Authorization': f'Bearer {token_hs384}'})
    assert response.status_code == 401
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert data["error"]["message"] == "Invalid token algorithm"


# ==============================================================================
# 5. Tes Malformed Token
# ==============================================================================

def test_malformed_token_returns_401(client):
    """Token dengan format acak atau korup wajib menghasilkan 401 Invalid token format."""
    bad_tokens = [
        "not-a-token",
        "invalid.jwt",
        "foo.bar.baz.extra",
        "!!!.@@@.###"
    ]
    for bad in bad_tokens:
        response = client.get('/api/protected', headers={'Authorization': f'Bearer {bad}'})
        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "UNAUTHORIZED"
        assert data["error"]["message"] == "Invalid token format"


# ==============================================================================
# 6. Tes Penegakan AUTH_REQUIRED
# ==============================================================================

def test_auth_required_blocks_request_without_header(client):
    """Ketika AUTH_REQUIRED=True, request tanpa header Authorization diblokir dengan 401."""
    response = client.get('/api/protected')
    assert response.status_code == 401
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["message"] == "Missing Authorization header"


def test_auth_required_blocks_invalid_header_format(client):
    """Header yang bukan format Bearer diblokir dengan 401."""
    response = client.get('/api/protected', headers={'Authorization': 'Basic dXNlcjpwYXNz'})
    assert response.status_code == 401
    data = response.get_json()
    assert data["error"]["message"] == "Invalid Authorization header format"


def test_auth_required_blocks_empty_token(client):
    """Header Bearer tanpa token diblokir dengan 401."""
    response = client.get('/api/protected', headers={'Authorization': 'Bearer '})
    assert response.status_code == 401
    data = response.get_json()
    assert data["error"]["message"] == "Empty token"


def test_auth_required_false_allows_unauthenticated(auth_app):
    """Ketika AUTH_REQUIRED=False dan tanpa header Authorization, request diizinkan (backward compat)."""
    auth_app.config['AUTH_REQUIRED'] = False
    test_client = auth_app.test_client()

    response = test_client.get('/api/protected')
    assert response.status_code == 200
    assert response.get_json()["success"] is True


# ==============================================================================
# 7. Tes Klaim Issuer (iss) dan Audience (aud)
# ==============================================================================

def test_issuer_claim_validation(auth_app):
    """Memverifikasi klaim issuer ketika JWT_ISSUER dikonfigurasi."""
    auth_app.config['JWT_ISSUER'] = 'mirofish-core'
    test_client = auth_app.test_client()

    # 1. Token dengan issuer valid
    valid_token = create_token(
        payload={"user_id": "usr_iss_ok", "iss": "mirofish-core"},
        secret_key=TEST_SECRET,
        expires_in=3600
    )
    resp_ok = test_client.get('/api/protected', headers={'Authorization': f'Bearer {valid_token}'})
    assert resp_ok.status_code == 200

    # 2. Token dengan issuer salah
    bad_iss_token = create_token(
        payload={"user_id": "usr_iss_bad", "iss": "untrusted-issuer"},
        secret_key=TEST_SECRET,
        expires_in=3600
    )
    resp_bad = test_client.get('/api/protected', headers={'Authorization': f'Bearer {bad_iss_token}'})
    assert resp_bad.status_code == 401
    assert resp_bad.get_json()["error"]["message"] == "Invalid token issuer"


def test_audience_claim_validation(auth_app):
    """Memverifikasi klaim audience ketika JWT_AUDIENCE dikonfigurasi."""
    auth_app.config['JWT_AUDIENCE'] = 'mirofish-api-v3'
    test_client = auth_app.test_client()

    # 1. Token dengan audience valid
    valid_token = create_token(
        payload={"user_id": "usr_aud_ok", "aud": "mirofish-api-v3"},
        secret_key=TEST_SECRET,
        expires_in=3600
    )
    resp_ok = test_client.get('/api/protected', headers={'Authorization': f'Bearer {valid_token}'})
    assert resp_ok.status_code == 200

    # 2. Token dengan audience salah
    bad_aud_token = create_token(
        payload={"user_id": "usr_aud_bad", "aud": "wrong-audience"},
        secret_key=TEST_SECRET,
        expires_in=3600
    )
    resp_bad = test_client.get('/api/protected', headers={'Authorization': f'Bearer {bad_aud_token}'})
    assert resp_bad.status_code == 401
    assert resp_bad.get_json()["error"]["message"] == "Invalid token audience"


# ==============================================================================
# 8. Tes Langsung decode_token & Pinning Algoritma
# ==============================================================================

def test_direct_decode_token_algorithm_pinning():
    """decode_token wajib hanya menerima algoritma yang dipin (HS256)."""
    assert ALLOWED_JWT_ALGORITHMS == ["HS256"]

    # Decode token valid secara langsung
    tok = create_token({"user_id": "direct_test"}, secret_key=TEST_SECRET, expires_in=600)
    decoded = decode_token(tok, secret_key=TEST_SECRET)
    assert decoded["user_id"] == "direct_test"

    # Token dengan algoritma non-HS256 ditolak dengan InvalidAlgorithmError
    tok_alt = jwt.encode({"user_id": "direct_alt"}, TEST_SECRET, algorithm="HS384")
    with pytest.raises(jwt.InvalidAlgorithmError):
        decode_token(tok_alt, secret_key=TEST_SECRET)
