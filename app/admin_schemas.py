from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCreateRequest(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    limite_diario: Optional[int] = None
    limite_por_minuto: Optional[int] = None


class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    activo: bool
    descripcion: Optional[str] = None
    fecha_creacion: datetime
    ultimo_uso: Optional[datetime] = None
    limite_diario: Optional[int] = None
    limite_por_minuto: Optional[int] = None
    consultas_realizadas: int
    ultima_ip: Optional[str] = None


class ApiKeyCreatedResponse(ApiKeyResponse):
    api_key: str


class ApiKeyStatsResponse(BaseModel):
    id: int
    nombre: str
    consultas_realizadas: int
    limite_diario: Optional[int] = None
    limite_por_minuto: Optional[int] = None
    ultimo_uso: Optional[datetime] = None
    ultima_ip: Optional[str] = None


class ApiLogResponse(BaseModel):
    id: int
    api_key_id: Optional[int] = None
    dni_consultado: Optional[str] = None
    endpoint: str
    metodo: str
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    codigo_http: int
    tiempo_respuesta_ms: int
    origen: Optional[str] = None
    fecha: datetime
