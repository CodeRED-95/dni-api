from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class DniBase(BaseModel):
    dni: str = Field(..., min_length=8, max_length=8, pattern=r"^\d{8}$")
    perudevs_id: Optional[str] = None
    nombres: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    nombre_completo: str
    genero: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    codigo_verificacion: Optional[str] = None
    fuente: str


class DniResponse(DniBase):
    fecha_consulta: datetime
    fecha_actualizacion: datetime

    model_config = ConfigDict(from_attributes=True)


class DniSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dni: str
    nombres: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    nombre_completo: str
    genero: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    codigo_verificacion: Optional[str] = None
    fuente: str
    fecha_consulta: datetime
    fecha_actualizacion: datetime


class HealthResponse(BaseModel):
    status: str
    database: str


class ErrorResponse(BaseModel):
    detail: str
