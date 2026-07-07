# Pruebas locales sin Docker

Esta guía sirve para ejecutar y validar `dni-api` en local antes de usar Docker.

## 1) Instalar dependencias

Crear un entorno virtual:

```powershell
python -m venv .venv
```

Activarlo:

```powershell
.venv\Scripts\Activate.ps1
```

Si prefieres cmd.exe:

```powershell
.\.venv\Scripts\activate
```

Instalar dependencias:

```powershell
pip install -r requirements.txt
```

## 2) Configurar variables de entorno

1. Copia `.env.example` a `.env`
2. Ajusta los valores locales
3. No uses tokens reales en el archivo de ejemplo

Variables importantes:

- `DATABASE_URL`
- `API_ADMIN_KEY`
- `HASH_SECRET`
- `PERUDEVS_TOKEN`
- `REDIS_URL`
- `REDIS_ENABLED`

Si no defines `DATABASE_URL`, la app usa por defecto `sqlite:///./local.db` y crea el archivo automáticamente.
Con SQLite no hace falta instalar PostgreSQL.

## 3) Iniciar el servidor local

Con el entorno virtual activo:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Abrir:

- `http://127.0.0.1:8000/web`
- `http://127.0.0.1:8000/admin-web`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/status`
- `http://127.0.0.1:8000/static/css/styles.css`
- `http://127.0.0.1:8000/static/js/web.js`
- `http://127.0.0.1:8000/static/css/admin.css`
- `http://127.0.0.1:8000/static/js/admin.js`

## 3.1) Verificar que se creó `local.db`

La primera vez que arranques con SQLite, la app crea `local.db` en la raíz del proyecto.
Si quieres reiniciar los datos locales, borra ese archivo y vuelve a iniciar el servidor.

## 4) Probar con curl

### Health

```powershell
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/status
```

### UI

```powershell
curl http://127.0.0.1:8000/web
curl http://127.0.0.1:8000/admin-web
curl http://127.0.0.1:8000/static/css/styles.css
curl http://127.0.0.1:8000/static/js/web.js
curl http://127.0.0.1:8000/static/css/admin.css
curl http://127.0.0.1:8000/static/js/admin.js
```

### Consulta DNI

```powershell
curl -H "X-API-Key: TU_API_KEY" http://127.0.0.1:8000/dni/12345678
```

### Admin

```powershell
curl -H "X-Admin-Key: TU_API_ADMIN_KEY" http://127.0.0.1:8000/admin/status
```

## 5) Prueba automática básica

Ejecuta este comando con el servidor ya levantado:

```powershell
python scripts\test_local.py
```

Opcionalmente define:

- `LOCAL_BASE_URL` para cambiar la URL base
- `LOCAL_TEST_DNI` para usar otro DNI
- `LOCAL_API_KEY` para la API key pública
- `LOCAL_ADMIN_KEY` para la clave admin

Si `LOCAL_API_KEY` o `LOCAL_ADMIN_KEY` no están definidos, el script saltará esas pruebas y seguirá validando `/health`, `/web` y `/admin-web`.

El CSS y JS públicos están en:

- `/static/css/styles.css`
- `/static/css/admin.css`
- `/static/js/web.js`
- `/static/js/admin.js`

## 6) Comando recomendado antes de subir a Docker

1. Levanta el servidor local
2. Ejecuta:

```powershell
python scripts\test_local.py
```

Si todos los checks salen `OK`, ya puedes seguir con Docker.
