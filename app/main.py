from fastapi import FastAPI

from app.database import Base, engine
from app.routes.dni import router as dni_router


app = FastAPI(
    title="API DNI Perú",
    version="1.0.0",
    description="API profesional para consulta de DNI en Perú con caché local y fallback a PeruDevs.",
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


app.include_router(dni_router)
