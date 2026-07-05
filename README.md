# API DNI Perú

API profesional en FastAPI para consulta de DNI con prioridad en base local y fallback a PeruDevs.

## Características

- FastAPI con Swagger automático en `/docs`
- PostgreSQL con persistencia
- Validación de DNI de 8 dígitos
- Seguridad básica con `X-API-Key`
- Servicio separado para PeruDevs
- Caché local de respuestas exitosas
- Búsqueda local por nombre o apellidos
- Docker y Docker Compose listos para Debian o Portainer

## Estructura

```text
dni-api/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── security.py
│   ├── routes/
│   │   └── dni.py
│   └── services/
│       └── perudevs.py
├── sql/
│   └── schema.sql
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Configuración

1. Copia `.env.example` a `.env`.
2. Completa estos valores:
- `API_KEY`
- `API_ADMIN_KEY`
- `DEFAULT_DAILY_LIMIT`
- `DEFAULT_MINUTE_LIMIT`
- `TOKEN_LENGTH`
- `HASH_SECRET`
- `PERUDEVS_TOKEN`
- Opcionalmente `DATABASE_URL`, `PERUDEVS_BASE_URL`, `PERUDEVS_TIMEOUT`

Ejemplo:

```env
POSTGRES_DB=dni_api
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/dni_api
API_ADMIN_KEY=mi_admin_key_segura
DEFAULT_DAILY_LIMIT=1000
DEFAULT_MINUTE_LIMIT=60
TOKEN_LENGTH=64
HASH_SECRET=mi_secreto_largo_y_unico
PERUDEVS_TOKEN=mi_token_real
PERUDEVS_BASE_URL=https://api.perudevs.com/api/v1/dni/complete
PERUDEVS_TIMEOUT=10
```

## Levantar con Docker Compose

```bash
docker compose up -d --build
```

La API quedará disponible en:

- `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`

## Endpoints

### `GET /health`
Verifica API y base de datos.

### `GET /dni/{dni}`
Busca primero en PostgreSQL. Si no existe, consulta PeruDevs, guarda si fue exitoso y devuelve la respuesta.

### `GET /dni/{dni}/refresh`
Fuerza una consulta nueva a PeruDevs y actualiza la base local.

### `GET /buscar?nombre=texto`
Busca por nombre, apellido paterno, apellido materno o nombre completo en la base local.

## Autenticación

Todos los endpoints están protegidos con `X-API-Key`.

Ejemplo de header:

```http
X-API-Key: mi_clave_segura
```

Si la clave es incorrecta, la API responde `401`.

## Administración

Los endpoints `/admin/*` usan `X-Admin-API-Key`.

Ejemplo:

```http
X-Admin-API-Key: mi_admin_key_segura
```

## Probar en Swagger

1. Abre `/docs`
2. Usa `Authorize` si tu cliente lo requiere
3. Envía el header `X-API-Key`
4. Prueba:
   - `GET /health`
   - `GET /dni/12345678`
   - `GET /dni/12345678/refresh`
   - `GET /buscar?nombre=juan`

## Consultar un DNI

```bash
curl -H "X-API-Key: mi_clave_segura" http://localhost:8000/dni/12345678
```

## Forzar actualización desde PeruDevs

```bash
curl -H "X-API-Key: mi_clave_segura" http://localhost:8000/dni/12345678/refresh
```

## Buscar por nombre en base local

```bash
curl -H "X-API-Key: mi_clave_segura" "http://localhost:8000/buscar?nombre=juan"
```

## Ejemplos

### curl

```bash
curl -H "X-API-Key: TU_API_KEY" http://localhost:8000/dni/12345678
```

### Python

```python
import requests

r = requests.get(
    "http://localhost:8000/dni/12345678",
    headers={"X-API-Key": "TU_API_KEY"},
    timeout=30,
)
print(r.json())
```

### JavaScript

```javascript
fetch("http://localhost:8000/dni/12345678", {
  headers: { "X-API-Key": "TU_API_KEY" }
}).then(r => r.json()).then(console.log)
```

## Notas de despliegue

- La tabla se crea automáticamente al iniciar la API.
- También se incluye `sql/schema.sql` para despliegues manuales.
- El volumen `postgres_data` mantiene la base persistente.
