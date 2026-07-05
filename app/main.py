from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.database import Base, engine
from app.middleware import ApiAuthLogMiddleware
from app.routes.admin import router as admin_router
from app.routes.dni import router as dni_router


app = FastAPI(
    title="API DNI Perú",
    version="1.0.0",
    description="API profesional para consulta de DNI en Perú con caché local y fallback a PeruDevs.",
)

app.add_middleware(ApiAuthLogMiddleware)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


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
        "description": "Token obligatorio para endpoints públicos.",
    }
    schema["security"] = [{"ApiKeyAuth": []}]
    for path, methods in schema.get("paths", {}).items():
        for method_name, operation in methods.items():
            if path.startswith("/admin"):
                operation["security"] = [{"AdminApiKey": []}]
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
