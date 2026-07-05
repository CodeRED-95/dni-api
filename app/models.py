from sqlalchemy import Column, DateTime, Integer, String, func, Index

from app.database import Base


class DniConsult(Base):
    __tablename__ = "dni_consultas"

    id = Column(Integer, primary_key=True, index=True)
    perudevs_id = Column(String(100), nullable=True, index=True)
    dni = Column(String(8), unique=True, nullable=False, index=True)
    nombres = Column(String(120), nullable=False)
    apellido_paterno = Column(String(120), nullable=True)
    apellido_materno = Column(String(120), nullable=True)
    nombre_completo = Column(String(255), nullable=False, index=True)
    genero = Column(String(20), nullable=True)
    fecha_nacimiento = Column(String(20), nullable=True)
    codigo_verificacion = Column(String(20), nullable=True)
    fuente = Column(String(50), nullable=False)
    fecha_consulta = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_actualizacion = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_dni_consultas_nombre_completo", "nombre_completo"),
    )
