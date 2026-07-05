import time
from datetime import datetime, timezone

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.auth import get_api_key_by_raw
from app.database import SessionLocal
from app.logging_utils import create_api_log


PUBLIC_PATH_PREFIXES = ("/docs", "/redoc", "/openapi.json")
SKIP_AUTH_PREFIXES = ("/admin",)


class ApiAuthLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith(PUBLIC_PATH_PREFIXES) or request.url.path.startswith(SKIP_AUTH_PREFIXES):
            return await call_next(request)

        start = time.perf_counter()
        response = None
        api_key = None
        raw_key = request.headers.get("x-api-key")
        dni_consultado = None
        path_parts = [part for part in request.url.path.split("/") if part]
        if len(path_parts) >= 2 and path_parts[0] == "dni":
            dni_consultado = path_parts[1]

        with SessionLocal() as db:
            if raw_key:
                api_key = get_api_key_by_raw(db, raw_key)
            request.state.api_key = api_key

        try:
            if api_key is None:
                response = JSONResponse(status_code=401, content={"detail": "API Key inválida."})
            elif not api_key.activo:
                response = JSONResponse(status_code=401, content={"detail": "API Key deshabilitada."})
            else:
                response = await call_next(request)
            return response
        finally:
            duration_ms = int((time.perf_counter() - start) * 1000)
            with SessionLocal() as db:
                if api_key is not None and response is not None and response.status_code < 400:
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
                    codigo_http=response.status_code if response is not None else 500,
                    tiempo_respuesta_ms=duration_ms,
                    origen=getattr(request.state, "origen", None),
                )
                db.commit()
