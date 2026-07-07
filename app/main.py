from fastapi import FastAPI, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import SQLAlchemyError
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.middleware import ApiAuthLogMiddleware
from app.routes.admin import router as admin_router
from app.routes.dni import router as dni_router
from app.services.cache import ping as redis_ping
from app.web import router as web_router


app = FastAPI(
    title="API DNI Perú",
    version="1.0.0",
    description="API profesional para consulta de DNI en Perú con caché local y fallback a PeruDevs.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://docs.codered.host",
        "https://codered.host",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ApiAuthLogMiddleware)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
def startup() -> None:
    try:
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as exc:
        raise RuntimeError(
            "No se pudo inicializar la base de datos. Revisa DATABASE_URL. "
            "Para desarrollo local puedes usar sqlite:///./local.db."
        ) from exc


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/web", status_code=307)


@app.get("/health")
def health():
    db_ok = True
    db_error = None
    try:
        from app.database import ping_database

        db_ok = ping_database()
    except Exception as exc:
        db_ok = False
        db_error = "No se pudo comprobar la base de datos."
    redis_ok = "ok" if redis_ping() else None
    payload = {"status": "ok" if db_ok else "degraded", "database": "ok" if db_ok else "fail", "redis": redis_ok}
    if db_error:
        payload["message"] = db_error
    return payload


@app.get("/status", include_in_schema=False)
def status():
    return {"status": "ok", "service": "dni-api"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


@app.options("/{full_path:path}", include_in_schema=False)
def options_handler(full_path: str):
    return Response(status_code=204)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema.setdefault("components", {}).setdefault("securitySchemes", {})["ApiKeyAuth"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "Token obligatorio para endpoints de consulta DNI.",
    }
    schema["security"] = []
    for path, methods in schema.get("paths", {}).items():
        for method_name, operation in methods.items():
            if path.startswith("/admin"):
                operation["security"] = [{"AdminApiKey": []}]
            elif path.startswith("/dni") or path.startswith("/buscar"):
                operation["security"] = [{"ApiKeyAuth": []}]
    schema["components"]["securitySchemes"]["AdminApiKey"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-Admin-API-Key",
        "description": "Token administrativo para gestionar API Keys.",
    }
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
app.include_router(dni_router)
app.include_router(admin_router)
app.include_router(web_router)
