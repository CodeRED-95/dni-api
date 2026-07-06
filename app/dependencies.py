from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import can_use_api_key, get_api_key_by_raw, validate_admin_key
from app.database import SessionLocal
from app.models import ApiKey, ApiLog


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_api_key(
    request: Request,
    x_api_key: str = Header(default=""),
    db: Session = Depends(get_db),
) -> ApiKey:
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API Key requerida.")
    api_key = get_api_key_by_raw(db, x_api_key)
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API Key inválida.")

    now = datetime.now(timezone.utc)
    day_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    minute_start = now - timedelta(minutes=1)
    daily_count = db.query(func.count(ApiLog.id)).filter(
        ApiLog.api_key_id == api_key.id,
        ApiLog.fecha >= day_start,
    ).scalar() or 0
    minute_count = db.query(func.count(ApiLog.id)).filter(
        ApiLog.api_key_id == api_key.id,
        ApiLog.fecha >= minute_start,
    ).scalar() or 0

    if api_key.limite_diario is not None and daily_count >= api_key.limite_diario:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Límite diario alcanzado.")
    if api_key.limite_por_minuto is not None and minute_count >= api_key.limite_por_minuto:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Límite por minuto alcanzado.")

    allowed, reason = can_use_api_key(api_key)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=reason)
    request.state.api_key = api_key
    return api_key


def require_admin_key(x_admin_api_key: str = Header(default="", alias="X-Admin-API-Key")) -> None:
    validate_admin_key(x_admin_api_key)
