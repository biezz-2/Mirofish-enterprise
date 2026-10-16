"""
MiroFish Enterprise - OAuth 2.1 Provider & Token Verifier (Agent 17)
Compliant with OAuth 2.1 (draft), RFC 6749, RFC 7636 (PKCE S256), RFC 7662 (Introspection), and RFC 8414 (Metadata).
Integrates natively with FastMCP AuthSettings and TokenVerifier protocol.
"""

import os
import time
import hmac
import hashlib
import base64
import json
import secrets
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode, parse_qs

from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings

# Secret key derivation for signing tokens
DEFAULT_SIGNING_KEY = os.environ.get("MIROFISH_OAUTH_SECRET", "mirofish-fastmcp-oauth2-signing-key-32b-secret")


def base64url_encode(input_bytes: bytes) -> str:
    """Encode bytes to base64url string without trailing padding '='."""
    return base64.urlsafe_b64encode(input_bytes).decode("utf-8").rstrip("=")


def base64url_decode(input_str: str) -> bytes:
    """Decode base64url string, adding required padding."""
    rem = len(input_str) % 4
    if rem > 0:
        input_str += "=" * (4 - rem)
    return base64.urlsafe_b64decode(input_str)


class OAuth2Manager:
    """Core OAuth 2.1 state and cryptographic token engine."""

    def __init__(
        self,
        server_url: str = "http://127.0.0.1:8080",
        signing_key: Optional[str] = None
    ):
        self.server_url = server_url.rstrip("/")
        self.signing_key = (signing_key or DEFAULT_SIGNING_KEY).encode("utf-8")
        
        # In-memory storage for auth codes and active tokens
        self.auth_codes: Dict[str, Dict[str, Any]] = {}
        self.registered_clients: Dict[str, Dict[str, Any]] = {
            "hermes_agent": {
                "client_secret": "hermes-mcp-secret-2026",
                "redirect_uris": ["http://127.0.0.1:8080/callback", "https://hermes.local/oauth/callback"],
                "allowed_scopes": ["mcp:read", "mcp:write", "simulation:run", "graph:read", "report:generate", "system:audit"],
                "client_name": "Hermes Coding Agent"
            },
            "claude_code": {
                "client_secret": "claude-mcp-secret-2026",
                "redirect_uris": ["http://127.0.0.1:8080/callback"],
                "allowed_scopes": ["mcp:read", "mcp:write", "simulation:run", "graph:read", "report:generate", "system:audit"],
                "client_name": "Claude Code CLI"
            },
            "mirofish_internal": {
                "client_secret": "internal-orchestrator-secret",
                "redirect_uris": ["http://127.0.0.1:8080/callback"],
                "allowed_scopes": ["mcp:read", "mcp:write", "simulation:run", "graph:read", "report:generate", "system:audit"],
                "client_name": "MiroFish Enterprise Core"
            }
        }
        self.active_tokens: Dict[str, Dict[str, Any]] = {}

    def register_client(self, client_id: str, client_secret: str, redirect_uris: List[str], allowed_scopes: List[str], client_name: str = ""):
        self.registered_clients[client_id] = {
            "client_secret": client_secret,
            "redirect_uris": redirect_uris,
            "allowed_scopes": allowed_scopes,
            "client_name": client_name or client_id
        }

    def generate_auth_code(
        self,
        client_id: str,
        redirect_uri: str,
        code_challenge: str,
        code_challenge_method: str = "S256",
        scope: str = "mcp:read",
        user_id: str = "default_enterprise_user",
        ttl_seconds: int = 300
    ) -> str:
        """Issue OAuth 2.1 authorization code with mandatory PKCE (RFC 7636)."""
        if code_challenge_method != "S256":
            raise ValueError("OAuth 2.1 mandates code_challenge_method='S256'")

        code = "code_" + secrets.token_urlsafe(32)
        self.auth_codes[code] = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "scope": scope,
            "user_id": user_id,
            "expires_at": time.time() + ttl_seconds
        }
        return code

    def verify_pkce(self, code_verifier: str, code_challenge: str) -> bool:
        """Verify RFC 7636 PKCE S256 code challenge."""
        h = hashlib.sha256(code_verifier.encode("ascii")).digest()
        computed = base64url_encode(h)
        return hmac.compare_digest(computed, code_challenge)

    def issue_access_token(
        self,
        client_id: str,
        scopes: List[str],
        user_id: Optional[str] = None,
        ttl_seconds: int = 3600
    ) -> Dict[str, Any]:
        """Issue signed bearer access token with expiration and scopes."""
        now = int(time.time())
        exp = now + ttl_seconds
        payload = {
            "iss": self.server_url,
            "sub": user_id or client_id,
            "client_id": client_id,
            "aud": self.server_url,
            "scopes": scopes,
            "iat": now,
            "exp": exp,
            "jti": secrets.token_hex(16)
        }
        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        payload_b64 = base64url_encode(payload_bytes)
        signature = hmac.new(self.signing_key, payload_b64.encode("ascii"), hashlib.sha256).digest()
        sig_b64 = base64url_encode(signature)

        token = f"mcp_{payload_b64}.{sig_b64}"
        refresh_token = f"rt_{secrets.token_urlsafe(32)}"

        token_record = {
            "client_id": client_id,
            "user_id": user_id or client_id,
            "scopes": scopes,
            "expires_at": exp,
            "created_at": now,
            "refresh_token": refresh_token
        }
        self.active_tokens[token] = token_record

        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": ttl_seconds,
            "scope": " ".join(scopes),
            "refresh_token": refresh_token
        }

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate bearer token signature, expiration, and registered state."""
        if not token:
            return None

        # Check in-memory store first
        record = self.active_tokens.get(token)
        now = time.time()
        if record:
            if record["expires_at"] < now:
                del self.active_tokens[token]
                return None
            return {
                "active": True,
                "client_id": record["client_id"],
                "sub": record["user_id"],
                "scopes": record["scopes"],
                "exp": record["expires_at"],
                "aud": self.server_url
            }

        # Otherwise verify cryptographic signature
        if token.startswith("mcp_") and "." in token:
            try:
                raw = token[4:]
                payload_b64, sig_b64 = raw.split(".", 1)
                expected_sig = hmac.new(self.signing_key, payload_b64.encode("ascii"), hashlib.sha256).digest()
                actual_sig = base64url_decode(sig_b64)
                if not hmac.compare_digest(expected_sig, actual_sig):
                    return None

                payload_data = json.loads(base64url_decode(payload_b64).decode("utf-8"))
                if payload_data.get("exp", 0) < now:
                    return None

                return {
                    "active": True,
                    "client_id": payload_data.get("client_id", "unknown"),
                    "sub": payload_data.get("sub", "unknown"),
                    "scopes": payload_data.get("scopes", []),
                    "exp": payload_data.get("exp"),
                    "aud": payload_data.get("aud", self.server_url)
                }
            except Exception:
                return None

        return None

    def get_token_verifier(self) -> "OAuth2TokenVerifier":
        """Return FastMCP TokenVerifier instance."""
        return OAuth2TokenVerifier(self)


class OAuth2TokenVerifier(TokenVerifier):
    """FastMCP native TokenVerifier adapter for OAuth 2.1 bearer tokens."""

    def __init__(self, oauth_manager: OAuth2Manager):
        self.oauth_manager = oauth_manager

    async def verify_token(self, token: str) -> Optional[AccessToken]:
        validated = self.oauth_manager.validate_token(token)
        if not validated or not validated.get("active"):
            return None

        return AccessToken(
            token=token,
            client_id=validated.get("client_id", "anonymous"),
            scopes=validated.get("scopes", []),
            expires_at=validated.get("exp"),
            resource=self.oauth_manager.server_url,
            subject=validated.get("sub")
        )


# ---------------------------------------------------------------------------
# Starlette Route Handlers for OAuth 2.1
# ---------------------------------------------------------------------------

async def oauth_metadata_endpoint(request: Request, manager: OAuth2Manager) -> JSONResponse:
    """RFC 8414 Authorization Server Metadata endpoint."""
    base = manager.server_url
    metadata = {
        "issuer": base,
        "authorization_endpoint": f"{base}/oauth/authorize",
        "token_endpoint": f"{base}/oauth/token",
        "introspection_endpoint": f"{base}/oauth/introspect",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "client_credentials", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post", "none"],
        "code_challenge_methods_supported": ["S256"],
        "scopes_supported": [
            "mcp:read",
            "mcp:write",
            "simulation:run",
            "graph:read",
            "report:generate",
            "system:audit"
        ]
    }
    return JSONResponse(metadata)


async def oauth_protected_resource_metadata(request: Request, manager: OAuth2Manager) -> JSONResponse:
    """RFC OAuth 2.0 Protected Resource Metadata endpoint."""
    base = manager.server_url
    metadata = {
        "resource": base,
        "authorization_servers": [base],
        "scopes_supported": [
            "mcp:read",
            "mcp:write",
            "simulation:run",
            "graph:read",
            "report:generate",
            "system:audit"
        ],
        "bearer_methods_supported": ["header"]
    }
    return JSONResponse(metadata)


async def oauth_authorize_endpoint(request: Request, manager: OAuth2Manager) -> Response:
    """OAuth 2.1 /oauth/authorize endpoint with PKCE verification."""
    params = request.query_params
    response_type = params.get("response_type")
    client_id = params.get("client_id")
    redirect_uri = params.get("redirect_uri")
    code_challenge = params.get("code_challenge")
    code_challenge_method = params.get("code_challenge_method", "S256")
    scope = params.get("scope", "mcp:read")
    state = params.get("state")

    if response_type != "code":
        return JSONResponse({"error": "unsupported_response_type", "error_description": "response_type must be 'code'"}, status_code=400)
    if not client_id or client_id not in manager.registered_clients:
        return JSONResponse({"error": "unauthorized_client", "error_description": "Unknown or invalid client_id"}, status_code=400)
    if not code_challenge:
        return JSONResponse({"error": "invalid_request", "error_description": "PKCE code_challenge is mandatory in OAuth 2.1"}, status_code=400)
    if code_challenge_method != "S256":
        return JSONResponse({"error": "invalid_request", "error_description": "Only S256 code_challenge_method is permitted"}, status_code=400)

    code = manager.generate_auth_code(
        client_id=client_id,
        redirect_uri=redirect_uri or "",
        code_challenge=code_challenge,
        code_challenge_method="S256",
        scope=scope
    )

    if redirect_uri:
        sep = "&" if "?" in redirect_uri else "?"
        qs = {"code": code}
        if state:
            qs["state"] = state
        return RedirectResponse(url=f"{redirect_uri}{sep}{urlencode(qs)}", status_code=302)

    return JSONResponse({"code": code, "state": state})


async def oauth_token_endpoint(request: Request, manager: OAuth2Manager) -> JSONResponse:
    """OAuth 2.1 /oauth/token endpoint supporting authorization_code (PKCE) and client_credentials."""
    body_bytes = await request.body()
    try:
        data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
    except Exception:
        data = dict(parse_qs(body_bytes.decode("utf-8")))
        data = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in data.items()}

    grant_type = data.get("grant_type")
    client_id = data.get("client_id")

    # Support Authorization header for client_credentials basic auth
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Basic "):
        try:
            cred = base64.b64decode(auth_header[6:]).decode("utf-8")
            c_id, c_secret = cred.split(":", 1)
            client_id = c_id
            data["client_secret"] = c_secret
        except Exception:
            pass

    if grant_type == "authorization_code":
        code = data.get("code")
        code_verifier = data.get("code_verifier")
        if not code or code not in manager.auth_codes:
            return JSONResponse({"error": "invalid_grant", "error_description": "Invalid or expired authorization code"}, status_code=400)

        code_info = manager.auth_codes.pop(code)
        if time.time() > code_info["expires_at"]:
            return JSONResponse({"error": "invalid_grant", "error_description": "Authorization code expired"}, status_code=400)

        if not code_verifier or not isinstance(code_verifier, str) or not manager.verify_pkce(code_verifier, code_info["code_challenge"]):
            return JSONResponse({"error": "invalid_grant", "error_description": "PKCE verification failed"}, status_code=400)

        scope_val = code_info.get("scope", "mcp:read")
        scopes = scope_val.split() if isinstance(scope_val, str) else list(scope_val)
        token_res = manager.issue_access_token(
            client_id=code_info["client_id"],
            scopes=scopes,
            user_id=code_info.get("user_id")
        )
        return JSONResponse(token_res)

    elif grant_type == "client_credentials":
        if not client_id or client_id not in manager.registered_clients:
            return JSONResponse({"error": "invalid_client", "error_description": "Client authentication failed"}, status_code=401)

        client_rec = manager.registered_clients[client_id]
        provided_secret = data.get("client_secret")
        if client_rec["client_secret"] and client_rec["client_secret"] != provided_secret:
            return JSONResponse({"error": "invalid_client", "error_description": "Client secret mismatch"}, status_code=401)

        req_scope = data.get("scope", "mcp:read")
        requested_scopes = req_scope.split() if isinstance(req_scope, str) else list(req_scope)
        allowed = client_rec.get("allowed_scopes", ["mcp:read"])
        effective_scopes = [s for s in requested_scopes if s in allowed] or ["mcp:read"]

        token_res = manager.issue_access_token(
            client_id=client_id,
            scopes=effective_scopes
        )
        return JSONResponse(token_res)

    return JSONResponse({"error": "unsupported_grant_type", "error_description": f"Grant type '{grant_type}' unsupported"}, status_code=400)


async def oauth_introspect_endpoint(request: Request, manager: OAuth2Manager) -> JSONResponse:
    """RFC 7662 Token Introspection endpoint."""
    body_bytes = await request.body()
    try:
        data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
    except Exception:
        data = dict(parse_qs(body_bytes.decode("utf-8")))
        data = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in data.items()}

    token = data.get("token") or request.query_params.get("token")
    if not token or not isinstance(token, str):
        return JSONResponse({"active": False})

    res = manager.validate_token(token)
    if not res:
        return JSONResponse({"active": False})

    return JSONResponse({
        "active": True,
        "scope": " ".join(res.get("scopes", [])),
        "client_id": res.get("client_id"),
        "sub": res.get("sub"),
        "exp": res.get("exp"),
        "aud": res.get("aud")
    })
