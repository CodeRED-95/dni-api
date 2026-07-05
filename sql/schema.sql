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
