import time
from datetime import datetime, timezone

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.database import SessionLocal
from app.logging_utils import create_api_log


PUBLIC_PATH_PREFIXES = ("/docs", "/redoc", "/openapi.json", "/health", "/web", "/admin-web", "/static")
SKIP_AUTH_PREFIXES = ("/admin",)


class ApiAuthLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        dni_consultado = None
        path_parts = [part for part in request.url.path.split("/") if part]
        if len(path_parts) >= 2 and path_parts[0] == "dni":
            dni_consultado = path_parts[1]

        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = int((time.perf_counter() - start) * 1000)
            with SessionLocal() as db:
                api_key = getattr(request.state, "api_key", None)
                response_status = locals().get("response").status_code if "response" in locals() and locals().get("response") is not None else 500
                if api_key is not None and response_status < 400:
                    api_key.consultas_realizadas = (api_key.consultas_realizadas or 0) + 1
                    api_key.ultimo_uso = datetime.now(timezone.utc)
                    api_key.ultima_ip = request.client.host if request.client else None
                    db.add(api_key)
                create_api_log(
                    db,
                    api_key_id=api_key.id if api_key else None,
                    dni_consultado=dni_consultado,
                    endpoint=request.url.path,
                    metodo=request.method,
                    ip=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    codigo_http=response_status,
                    tiempo_respuesta_ms=duration_ms,
                    origen=getattr(request.state, "origen", None),
                )
                db.commit()
