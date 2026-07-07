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
- Redis para caché transparente de consultas DNI
- Docker y Docker Compose listos para Debian o Portainer

## Estructura

```text
dni-api/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── cache.py
│   ├── logging.py
│   ├── web.py
│   ├── middleware/
│   ├── routes/
│   │   ├── admin.py
│   │   └── dni.py
│   └── services/
│       ├── auth.py
│       ├── cache.py
│       ├── logging.py
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
- `API_ADMIN_KEY`
- `DEFAULT_DAILY_LIMIT`
- `DEFAULT_MINUTE_LIMIT`
- `TOKEN_LENGTH`
- `HASH_SECRET`
- `PERUDEVS_TOKEN`
- `REDIS_URL`
- `REDIS_ENABLED`
- `CACHE_TTL_SECONDS`
- `PGADMIN_DEFAULT_EMAIL`
- `PGADMIN_DEFAULT_PASSWORD`
- `DATABASE_URL`
- `PERUDEVS_BASE_URL`
- `PERUDEVS_TIMEOUT`

Ejemplo:

```env
POSTGRES_DB=dni_api
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
PGADMIN_DEFAULT_EMAIL=admin@local
PGADMIN_DEFAULT_PASSWORD=admin
DATABASE_URL=postgresql+psycopg://postgres:postgres@postgres:5432/dni_api
REDIS_URL=redis://redis:6379/0
REDIS_ENABLED=true
CACHE_TTL_SECONDS=3600
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
docker compose down --remove-orphans
docker compose up -d --build
```

La API quedará disponible en:

- `http://localhost:8000/` redirige a `/web`
- `http://localhost:8000`
- `http://localhost:8002`
- Swagger: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`
- Web: `http://localhost:8002/web`
- Admin Web: `http://localhost:8002/admin-web`
- pgAdmin: `http://localhost:8082`

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

También se acepta:

- `Authorization: Bearer MI_API_KEY`
- `?apikey=MI_API_KEY`
- `?token=MI_API_KEY`

Prioridad de lectura:

1. `Authorization: Bearer ...`
2. `?apikey=...`
3. `?token=...`

La autenticación se aplica solo a las rutas de consulta DNI, por ejemplo:

```http
GET /dni/71218478?apikey=MI_API_KEY
Authorization: Bearer MI_API_KEY
```

Las rutas públicas siguen sin pedir clave:

- `/web`
- `/docs`
- `/openapi.json`
- `/redoc`

La interfaz `/web` sí necesita una `X-API-Key` para consultar DNI.

## Administración

Los endpoints `/admin/*` usan `X-Admin-Key`.

La UI `/admin-web` muestra el estado de la API, configuración básica y estadísticas generales sin mostrar secretos completos.

Ejemplo:

```http
X-Admin-Key: mi_admin_key_segura
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

## Cloudflare Tunnel

Para publicar `https://dni.midominio.com` con Cloudflare Tunnel:

1. Instala `cloudflared` en el servidor.
2. Autentica el túnel:
   ```bash
   cloudflared tunnel login
   ```
3. Crea un túnel:
   ```bash
   cloudflared tunnel create dni-api
   ```
4. Asigna el hostname:
   ```bash
   cloudflared tunnel route dns dni-api dni.midominio.com
   ```
5. Configura el ingress para apuntar a `http://localhost:8002`.
6. Ejecuta el túnel con el archivo de configuración.

## Validación final

Ver `.env` local:

```bash
grep API_ADMIN_KEY .env
```

Ver variables dentro del contenedor:

```bash
docker compose exec api env | grep API_ADMIN_KEY
```

Ver puertos:

```bash
docker ps
```

Probar docs:

```bash
curl http://localhost:8002/docs
```

Probar admin key:

```bash
curl -X GET http://localhost:8002/admin/tokens \
  -H "X-Admin-Key: TU_API_ADMIN_KEY"
```

Si aparece un contenedor antiguo como `dni-api-db`:

```bash
docker rm -f dni-api-db
```

Verificar rápidamente que el contenedor usa la misma `API_ADMIN_KEY` que el `.env`:

```bash
grep '^API_ADMIN_KEY=' .env
docker compose exec api env | grep API_ADMIN_KEY
```

Si ambos valores difieren, recrea los contenedores:

```bash
docker compose down --remove-orphans
docker compose up -d --build
```

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
