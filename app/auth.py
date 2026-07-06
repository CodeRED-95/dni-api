import hashlib
import hmac
import os
import secrets
import string
from typing import Optional

from dotenv import load_dotenv
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import ApiKey


load_dotenv()

API_ADMIN_KEY = os.getenv("API_ADMIN_KEY", "")
DEFAULT_DAILY_LIMIT = int(os.getenv("DEFAULT_DAILY_LIMIT", "1000"))
DEFAULT_MINUTE_LIMIT = int(os.getenv("DEFAULT_MINUTE_LIMIT", "60"))
TOKEN_LENGTH = int(os.getenv("TOKEN_LENGTH", "64"))
HASH_SECRET = os.getenv("HASH_SECRET", "")


def _mask_length(value: str) -> int:
    return len(value or "")


def debug_admin_key_state() -> None:
    configured = bool(API_ADMIN_KEY.strip())
    print(
        f"[auth] API_ADMIN_KEY configured={configured} length={_mask_length(API_ADMIN_KEY)}"
    )


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
    return bool(API_ADMIN_KEY.strip()) and hmac.compare_digest((provided_key or "").strip(), API_ADMIN_KEY.strip())


def validate_admin_key(provided_key: str) -> bool:
    debug_admin_key_state()
    if not API_ADMIN_KEY.strip():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_ADMIN_KEY no configurada en el servidor",
        )
    if not hmac.compare_digest((provided_key or "").strip(), API_ADMIN_KEY.strip()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin API Key inválida.")
    return True


def get_api_key_by_raw(session: Session, raw_key: str) -> Optional[ApiKey]:
    hashed = hash_api_key(raw_key)
    return session.query(ApiKey).filter(ApiKey.api_key == hashed).one_or_none()


def can_use_api_key(api_key: ApiKey) -> tuple[bool, str]:
    if not api_key.activo:
        return False, "API Key deshabilitada."
    return True, ""
