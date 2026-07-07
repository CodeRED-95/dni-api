from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db, ping_database
from app.dependencies import get_current_api_key
from app.models import DniConsult
from app.schemas import DniResponse, DniSearchResult, HealthResponse
from app.services.cache import get_json, set_json
from app.services.perudevs import PeruDevsClient, PeruDevsError, PeruDevsNotFound


router = APIRouter(prefix="", tags=["DNI"])


def _public_payload(record: DniConsult | dict) -> dict:
    if isinstance(record, dict):
        source = record
    else:
        source = {
            "dni": record.dni,
            "nombres": record.nombres,
            "apellido_paterno": record.apellido_paterno,
            "apellido_materno": record.apellido_materno,
            "nombre_completo": record.nombre_completo,
            "genero": record.genero,
            "fecha_nacimiento": record.fecha_nacimiento,
            "codigo_verificacion": record.codigo_verificacion,
        }
    return {
        "dni": source.get("dni"),
        "nombres": source.get("nombres"),
        "apellido_paterno": source.get("apellido_paterno"),
        "apellido_materno": source.get("apellido_materno"),
        "nombre_completo": source.get("nombre_completo"),
        "genero": source.get("genero"),
        "fecha_nacimiento": source.get("fecha_nacimiento"),
        "codigo_verificacion": source.get("codigo_verificacion"),
    }


def validate_dni(dni: str) -> str:
    normalized = (dni or "").strip()
    if not normalized.isdigit() or len(normalized) != 8:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="El DNI debe tener exactamente 8 dígitos numéricos.")
    return normalized


def serialize(record: DniConsult) -> DniResponse:
    return DniResponse.model_validate(_public_payload(record))


def save_record(db: Session, payload: dict) -> DniConsult:
    now = datetime.now(timezone.utc)
    record = db.query(DniConsult).filter(DniConsult.dni == payload["dni"]).one_or_none()
    if record is None:
        record = DniConsult(**payload, fecha_consulta=now, fecha_actualizacion=now)
        db.add(record)
    else:
        record.perudevs_id = payload.get("perudevs_id")
        record.nombres = payload["nombres"]
        record.apellido_paterno = payload["apellido_paterno"]
        record.apellido_materno = payload["apellido_materno"]
        record.nombre_completo = payload["nombre_completo"]
        record.genero = payload.get("genero")
        record.fecha_nacimiento = payload.get("fecha_nacimiento")
        record.codigo_verificacion = payload.get("codigo_verificacion")
        record.fuente = payload["fuente"]
        record.fecha_actualizacion = now
    db.commit()
    db.refresh(record)
    return record


@router.get("/health", response_model=HealthResponse)
def health(request: Request, db: Session = Depends(get_db)):
    try:
        ping_database()
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="La base de datos no está disponible.")
    request.state.origen = "Base Local"
    return HealthResponse(status="ok", database="ok")


@router.get("/dni/{dni}", response_model=DniResponse)
def get_dni(dni: str, request: Request, db: Session = Depends(get_db), api_key=Depends(get_current_api_key)):
    dni = validate_dni(dni)
    cache_key = f"dni:{dni}"
    cached = get_json(cache_key)
    if cached is not None:
        request.state.origen = "Redis"
        public_cached = _public_payload(cached)
        if public_cached != cached:
            set_json(cache_key, public_cached)
        return public_cached

    record = db.query(DniConsult).filter(DniConsult.dni == dni).one_or_none()
    if record:
        request.state.origen = "Base Local"
        data = serialize(record).model_dump(mode="json")
        set_json(cache_key, data)
        return data

    client = PeruDevsClient()
    try:
        payload = client.get_dni(dni)
    except PeruDevsNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNI no encontrado.")
    except PeruDevsError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="No se pudo consultar la fuente externa.")

    record = save_record(db, payload)
    request.state.origen = "PeruDevs"
    data = serialize(record).model_dump(mode="json")
    set_json(cache_key, data)
    return data


@router.get("/dni/{dni}/refresh", response_model=DniResponse)
def refresh_dni(dni: str, request: Request, db: Session = Depends(get_db), api_key=Depends(get_current_api_key)):
    dni = validate_dni(dni)
    client = PeruDevsClient()
    try:
        payload = client.get_dni(dni)
    except PeruDevsNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNI no encontrado.")
    except PeruDevsError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="No se pudo consultar la fuente externa.")

    record = save_record(db, payload)
    request.state.origen = "PeruDevs"
    data = serialize(record).model_dump(mode="json")
    set_json(f"dni:{dni}", data)
    return data


@router.get("/buscar", response_model=list[DniSearchResult])
def buscar(request: Request, nombre: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    like = f"%{nombre.strip()}%"
    request.state.origen = "Base Local"
    results = (
        db.query(DniConsult)
        .filter(
            or_(
                DniConsult.nombres.ilike(like),
                DniConsult.apellido_paterno.ilike(like),
                DniConsult.apellido_materno.ilike(like),
                DniConsult.nombre_completo.ilike(like),
            )
        )
        .order_by(DniConsult.nombre_completo.asc())
        .all()
    )
    return [DniSearchResult.model_validate(_public_payload(row)) for row in results]
