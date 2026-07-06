from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.admin_schemas import ApiKeyCreateRequest, ApiKeyCreatedResponse, ApiKeyResponse, ApiKeyStatsResponse, ApiLogResponse
from app.auth import DEFAULT_DAILY_LIMIT, DEFAULT_MINUTE_LIMIT, generate_api_key, hash_api_key, debug_admin_key_state
from app.dependencies import get_db, require_admin_key
from app.models import ApiKey, ApiLog


router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_admin_key)])

debug_admin_key_state()


def _api_key_to_response(api_key: ApiKey) -> ApiKeyResponse:
    return ApiKeyResponse.model_validate(api_key)


@router.post("/api-keys", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(payload: ApiKeyCreateRequest, db: Session = Depends(get_db)):
    raw_key = generate_api_key()
    hashed = hash_api_key(raw_key)
    api_key = ApiKey(
        nombre=payload.nombre,
        api_key=hashed,
        activo=True,
        descripcion=payload.descripcion,
        limite_diario=payload.limite_diario if payload.limite_diario is not None else DEFAULT_DAILY_LIMIT,
        limite_por_minuto=payload.limite_por_minuto if payload.limite_por_minuto is not None else DEFAULT_MINUTE_LIMIT,
        consultas_realizadas=0,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return ApiKeyCreatedResponse(
        id=api_key.id,
        nombre=api_key.nombre,
        activo=api_key.activo,
        descripcion=api_key.descripcion,
        fecha_creacion=api_key.fecha_creacion,
        ultimo_uso=api_key.ultimo_uso,
        limite_diario=api_key.limite_diario,
        limite_por_minuto=api_key.limite_por_minuto,
        consultas_realizadas=api_key.consultas_realizadas,
        ultima_ip=api_key.ultima_ip,
        api_key=raw_key,
    )


@router.get("/api-keys", response_model=list[ApiKeyResponse])
def list_api_keys(db: Session = Depends(get_db)):
    return db.query(ApiKey).order_by(ApiKey.fecha_creacion.desc()).all()


@router.get("/api-keys/search", response_model=list[ApiKeyResponse])
def search_api_keys(nombre: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    like = f"%{nombre.strip()}%"
    return db.query(ApiKey).filter(ApiKey.nombre.ilike(like)).order_by(ApiKey.nombre.asc()).all()


@router.patch("/api-keys/{api_key_id}/activate", response_model=ApiKeyResponse)
def activate_api_key(api_key_id: int, db: Session = Depends(get_db)):
    api_key = db.query(ApiKey).filter(ApiKey.id == api_key_id).one_or_none()
    if api_key is None:
        raise HTTPException(status_code=404, detail="API Key no encontrada.")
    api_key.activo = True
    db.commit()
    db.refresh(api_key)
    return api_key


@router.patch("/api-keys/{api_key_id}/deactivate", response_model=ApiKeyResponse)
def deactivate_api_key(api_key_id: int, db: Session = Depends(get_db)):
    api_key = db.query(ApiKey).filter(ApiKey.id == api_key_id).one_or_none()
    if api_key is None:
        raise HTTPException(status_code=404, detail="API Key no encontrada.")
    api_key.activo = False
    db.commit()
    db.refresh(api_key)
    return api_key


@router.delete("/api-keys/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_api_key(api_key_id: int, db: Session = Depends(get_db)):
    api_key = db.query(ApiKey).filter(ApiKey.id == api_key_id).one_or_none()
    if api_key is None:
        raise HTTPException(status_code=404, detail="API Key no encontrada.")
    db.delete(api_key)
    db.commit()


@router.post("/api-keys/{api_key_id}/regenerate", response_model=ApiKeyCreatedResponse)
def regenerate_api_key(api_key_id: int, db: Session = Depends(get_db)):
    api_key = db.query(ApiKey).filter(ApiKey.id == api_key_id).one_or_none()
    if api_key is None:
        raise HTTPException(status_code=404, detail="API Key no encontrada.")
    raw_key = generate_api_key()
    api_key.api_key = hash_api_key(raw_key)
    api_key.consultas_realizadas = 0
    api_key.ultimo_uso = None
    db.commit()
    db.refresh(api_key)
    return ApiKeyCreatedResponse(
        id=api_key.id,
        nombre=api_key.nombre,
        activo=api_key.activo,
        descripcion=api_key.descripcion,
        fecha_creacion=api_key.fecha_creacion,
        ultimo_uso=api_key.ultimo_uso,
        limite_diario=api_key.limite_diario,
        limite_por_minuto=api_key.limite_por_minuto,
        consultas_realizadas=api_key.consultas_realizadas,
        ultima_ip=api_key.ultima_ip,
        api_key=raw_key,
    )


@router.get("/api-keys/{api_key_id}/stats", response_model=ApiKeyStatsResponse)
def api_key_stats(api_key_id: int, db: Session = Depends(get_db)):
    api_key = db.query(ApiKey).filter(ApiKey.id == api_key_id).one_or_none()
    if api_key is None:
        raise HTTPException(status_code=404, detail="API Key no encontrada.")
    return ApiKeyStatsResponse(
        id=api_key.id,
        nombre=api_key.nombre,
        consultas_realizadas=api_key.consultas_realizadas,
        limite_diario=api_key.limite_diario,
        limite_por_minuto=api_key.limite_por_minuto,
        ultimo_uso=api_key.ultimo_uso,
        ultima_ip=api_key.ultima_ip,
    )


@router.get("/api-keys/{api_key_id}/logs", response_model=list[ApiLogResponse])
def api_key_logs(api_key_id: int, db: Session = Depends(get_db)):
    return db.query(ApiLog).filter(ApiLog.api_key_id == api_key_id).order_by(ApiLog.fecha.desc()).all()
