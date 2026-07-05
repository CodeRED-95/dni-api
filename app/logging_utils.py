from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models import ApiLog


def create_api_log(
    session: Session,
    *,
    api_key_id: Optional[int],
    dni_consultado: Optional[str],
    endpoint: str,
    metodo: str,
    ip: Optional[str],
    user_agent: Optional[str],
    codigo_http: int,
    tiempo_respuesta_ms: int,
    origen: Optional[str],
) -> None:
    session.add(
        ApiLog(
            api_key_id=api_key_id,
            dni_consultado=dni_consultado,
            endpoint=endpoint,
            metodo=metodo,
            ip=ip,
            user_agent=user_agent,
            codigo_http=codigo_http,
            tiempo_respuesta_ms=tiempo_respuesta_ms,
            origen=origen,
            fecha=datetime.now(timezone.utc),
        )
    )
