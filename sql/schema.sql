CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL UNIQUE,
    api_key VARCHAR(64) NOT NULL UNIQUE,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    descripcion TEXT,
    fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ultimo_uso TIMESTAMPTZ,
    limite_diario INTEGER,
    limite_por_minuto INTEGER,
    consultas_realizadas INTEGER NOT NULL DEFAULT 0,
    ultima_ip VARCHAR(45)
);

CREATE TABLE IF NOT EXISTS api_logs (
    id SERIAL PRIMARY KEY,
    api_key_id INTEGER REFERENCES api_keys(id) ON DELETE SET NULL,
    dni_consultado VARCHAR(8),
    endpoint VARCHAR(255) NOT NULL,
    metodo VARCHAR(10) NOT NULL,
    ip VARCHAR(45),
    user_agent TEXT,
    codigo_http INTEGER NOT NULL,
    tiempo_respuesta_ms INTEGER NOT NULL DEFAULT 0,
    origen VARCHAR(50),
    fecha TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dni_consultas (
    id SERIAL PRIMARY KEY,
    perudevs_id VARCHAR(100),
    dni VARCHAR(8) NOT NULL UNIQUE,
    nombres VARCHAR(120) NOT NULL,
    apellido_paterno VARCHAR(120),
    apellido_materno VARCHAR(120),
    nombre_completo VARCHAR(255) NOT NULL,
    genero VARCHAR(20),
    fecha_nacimiento VARCHAR(20),
    codigo_verificacion VARCHAR(20),
    fuente VARCHAR(50) NOT NULL,
    fecha_consulta TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_dni_consultas_nombre_completo ON dni_consultas (nombre_completo);
CREATE INDEX IF NOT EXISTS ix_dni_consultas_dni ON dni_consultas (dni);
CREATE INDEX IF NOT EXISTS ix_api_logs_api_key_id ON api_logs (api_key_id);
CREATE INDEX IF NOT EXISTS ix_api_logs_fecha ON api_logs (fecha);
