import json
import os
import sys
import urllib.error
import urllib.request


BASE_URL = os.getenv("LOCAL_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
TEST_DNI = os.getenv("LOCAL_TEST_DNI", "12345678").strip()
API_KEY = os.getenv("LOCAL_API_KEY", "").strip()
ADMIN_KEY = os.getenv("LOCAL_ADMIN_KEY", "").strip()
TIMEOUT = float(os.getenv("LOCAL_TIMEOUT", "10"))


def request(path, headers=None):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.status, body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, body
    except Exception as exc:
        return None, str(exc)


def show(name, status, body):
    if status is None:
        print(f"[ERROR] {name}: {body}")
        return False
    preview = body.strip().replace("\n", " ")
    if len(preview) > 180:
        preview = preview[:180] + "..."
    print(f"[{ 'OK' if 200 <= status < 400 else 'ERROR' }] {name}: HTTP {status} -> {preview}")
    return 200 <= status < 400


def parse_json(body):
    try:
        return json.loads(body)
    except Exception:
        return None


def main():
    checks = []

    status_code, body = request("/status")
    checks.append(show("/status", status_code, body))

    status_code, body = request("/health")
    checks.append(show("/health", status_code, body))

    status_code, body = request("/web")
    checks.append(show("/web", status_code, body))

    status_code, body = request("/admin-web")
    checks.append(show("/admin-web", status_code, body))

    status_code, body = request("/static/css/styles.css")
    checks.append(show("/static/css/styles.css", status_code, body))

    status_code, body = request("/static/js/web.js")
    checks.append(show("/static/js/web.js", status_code, body))

    status_code, body = request("/static/css/admin.css")
    checks.append(show("/static/css/admin.css", status_code, body))

    status_code, body = request("/static/js/admin.js")
    checks.append(show("/static/js/admin.js", status_code, body))

    if not API_KEY:
        print("[INFO] LOCAL_API_KEY no configurada; salto la prueba /dni/{dni}.")
    else:
        status_code, body = request(f"/dni/{TEST_DNI}?apikey={API_KEY}", headers={"Accept": "application/json"})
        checks.append(show(f"/dni/{TEST_DNI}", status_code, body))
        data = parse_json(body)
        if status_code == 200 and isinstance(data, dict):
            print(f"[OK] DNI consultado: {data.get('dni', TEST_DNI)} | nombre={data.get('nombre_completo', '-')}")

    if ADMIN_KEY:
        status_code, body = request("/admin/status", headers={"X-Admin-Key": ADMIN_KEY, "Accept": "application/json"})
        checks.append(show("/admin/status", status_code, body))
    else:
        print("[INFO] LOCAL_ADMIN_KEY no configurada; salto la prueba /admin/status.")

    if all(checks):
        print("RESULTADO: OK")
        return 0

    print("RESULTADO: ERROR")
    return 1


if __name__ == "__main__":
    sys.exit(main())
