import hashlib
import hmac
import os
import secrets
import string
from typing import Optional

from dotenv import load_dotenv
from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.models import ApiKey


load_dotenv(override=False)

API_ADMIN_KEY = os.getenv("API_ADMIN_KEY", "")
DEFAULT_DAILY_LIMIT = int(os.getenv("DEFAULT_DAILY_LIMIT", "1000"))
DEFAULT_MINUTE_LIMIT = int(os.getenv("DEFAULT_MINUTE_LIMIT", "60"))
TOKEN_LENGTH = int(os.getenv("TOKEN_LENGTH", "64"))
HASH_SECRET = os.getenv("HASH_SECRET", "")


def _mask_length(value: str) -> int:
    return len(value or "")


def _mask_key(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    tail = value[-4:] if len(value) >= 4 else value
    return f"{'*' * max(len(value) - 4, 0)}{tail}"


def _require_hash_secret() -> None:
    if not HASH_SECRET:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="HASH_SECRET no configurado.")


def generate_api_key(length: Optional[int] = None) -> str:
    size = max(64, int(length or TOKEN_LENGTH))
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(size))


def hash_api_key(raw_key: str) -> str:
    _require_hash_secret()
    digest = hashlib.sha256(f"{HASH_SECRET}:{raw_key}".encode("utf-8")).hexdigest()
    return digest


def verify_raw_api_key(raw_key: str, stored_hash: str) -> bool:
    try:
        computed = hash_api_key(raw_key)
    except HTTPException:
        return False
    return hmac.compare_digest(computed, stored_hash)


def is_admin_key_valid(provided_key: str) -> bool:
    server_key = (API_ADMIN_KEY or "").strip().replace("\r", "").replace("\n", "")
    client_key = (provided_key or "").strip().replace("\r", "").replace("\n", "")
    return bool(server_key) and hmac.compare_digest(client_key, server_key)


def validate_admin_key(provided_key: str) -> bool:
    server_key = (API_ADMIN_KEY or "").strip().replace("\r", "").replace("\n", "")
    client_key = (provided_key or "").strip().replace("\r", "").replace("\n", "")
    if not server_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_ADMIN_KEY no configurada en el servidor",
        )
    if not hmac.compare_digest(client_key, server_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin API Key inválida.")
    return True


def extract_public_api_key(request: Request) -> str:
    authorization = (request.headers.get("authorization") or "").strip()
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    query_key = (request.query_params.get("apikey") or request.query_params.get("token") or "").strip()
    return query_key


def get_api_key_by_raw(session: Session, raw_key: str) -> Optional[ApiKey]:
    hashed = hash_api_key(raw_key)
    return session.query(ApiKey).filter(ApiKey.api_key == hashed).one_or_none()


def can_use_api_key(api_key: ApiKey) -> tuple[bool, str]:
    if not api_key.activo:
        return False, "API Key deshabilitada."
    return True, ""
