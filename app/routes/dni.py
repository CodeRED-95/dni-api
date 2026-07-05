from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db, ping_database
from app.models import DniConsult
from app.schemas import DniResponse, DniSearchResult, HealthResponse
from app.security import verify_api_key
from app.services.perudevs import PeruDevsClient, PeruDevsError, PeruDevsNotFound


router = APIRouter(prefix="", tags=["DNI"], dependencies=[Depends(verify_api_key)])


def validate_dni(dni: str) -> str:
    if not dni.isdigit() or len(dni) != 8:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="El DNI debe tener 8 dígitos numéricos.")
    return dni


def serialize(record: DniConsult) -> DniResponse:
    return DniResponse.model_validate(record)


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
def get_dni(dni: str, request: Request, db: Session = Depends(get_db)):
    dni = validate_dni(dni)
    record = db.query(DniConsult).filter(DniConsult.dni == dni).one_or_none()
    if record:
        request.state.origen = "Base Local"
        return serialize(record)

    client = PeruDevsClient()
    try:
        payload = client.get_dni(dni)
    except PeruDevsNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNI no encontrado.")
    except PeruDevsError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"No se pudo consultar PeruDevs: {exc}")

    record = save_record(db, payload)
    request.state.origen = "PeruDevs"
    return serialize(record)


@router.get("/dni/{dni}/refresh", response_model=DniResponse)
def refresh_dni(dni: str, request: Request, db: Session = Depends(get_db)):
    dni = validate_dni(dni)
    client = PeruDevsClient()
    try:
        payload = client.get_dni(dni)
    except PeruDevsNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNI no encontrado.")
    except PeruDevsError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"No se pudo consultar PeruDevs: {exc}")

    record = save_record(db, payload)
    request.state.origen = "PeruDevs"
    return serialize(record)


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
    return results
