from sqlalchemy import Column, DateTime, Integer, String, Boolean, Text, ForeignKey, func, Index

from app.database import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False, unique=True, index=True)
    api_key = Column(String(64), nullable=False, unique=True, index=True)
    activo = Column(Boolean, nullable=False, default=True)
    descripcion = Column(Text, nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ultimo_uso = Column(DateTime(timezone=True), nullable=True)
    limite_diario = Column(Integer, nullable=True)
    limite_por_minuto = Column(Integer, nullable=True)
    consultas_realizadas = Column(Integer, nullable=False, default=0)
    ultima_ip = Column(String(45), nullable=True)


class ApiLog(Base):
    __tablename__ = "api_logs"

    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True, index=True)
    dni_consultado = Column(String(8), nullable=True, index=True)
    endpoint = Column(String(255), nullable=False)
    metodo = Column(String(10), nullable=False)
    ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    codigo_http = Column(Integer, nullable=False)
    tiempo_respuesta_ms = Column(Integer, nullable=False, default=0)
    origen = Column(String(50), nullable=True)
    fecha = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


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
