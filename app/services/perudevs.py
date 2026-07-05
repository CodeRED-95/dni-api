import os
from typing import Any, Dict

from dotenv import load_dotenv
import httpx


load_dotenv()

class PeruDevsError(Exception):
    pass


class PeruDevsNotFound(PeruDevsError):
    pass


class PeruDevsClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("PERUDEVS_BASE_URL", "https://api.perudevs.com/api/v1/dni/complete")
        self.token = os.getenv("PERUDEVS_TOKEN", "")
        self.timeout = float(os.getenv("PERUDEVS_TIMEOUT", "10"))

    def _headers(self) -> Dict[str, str]:
        return {"Accept": "application/json"}

    def get_dni(self, dni: str) -> Dict[str, Any]:
        if not self.token:
            raise PeruDevsError("Token de PeruDevs no configurado.")
        url = f"{self.base_url.rstrip('/')}?document={dni}&key={self.token}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=self._headers())
        except httpx.TimeoutException as exc:
            raise PeruDevsError("Timeout al consultar PeruDevs.") from exc
        except httpx.RequestError as exc:
            raise PeruDevsError("Error de conexión con PeruDevs.") from exc

        if response.status_code == 404:
            raise PeruDevsNotFound("DNI no encontrado en PeruDevs.")
        if response.status_code >= 400:
            raise PeruDevsError("PeruDevs devolvió un error inesperado.")

        try:
            data = response.json()
        except ValueError as exc:
            raise PeruDevsError("Respuesta inválida de PeruDevs.") from exc

        return self._normalize_response(data, dni)

    def _normalize_response(self, data: Dict[str, Any], dni: str) -> Dict[str, Any]:
        if data.get("estado") is not True:
            raise PeruDevsNotFound(data.get("mensaje") or "DNI no encontrado en PeruDevs.")

        payload = data.get("resultado") or {}
        nombres = (payload.get("nombres") or "").strip()
        apellido_paterno = (payload.get("apellido_paterno") or "").strip() or None
        apellido_materno = (payload.get("apellido_materno") or "").strip() or None
        nombre_completo = (payload.get("nombre_completo") or "").strip()

        if not nombres or not apellido_paterno or not apellido_materno or not nombre_completo:
            raise PeruDevsError("PeruDevs no devolvió datos válidos.")

        return {
            "perudevs_id": str(payload.get("id") or "").strip() or None,
            "dni": dni,
            "nombres": nombres,
            "apellido_paterno": apellido_paterno,
            "apellido_materno": apellido_materno,
            "nombre_completo": nombre_completo,
            "genero": (payload.get("genero") or "").strip() or None,
            "fecha_nacimiento": (payload.get("fecha_nacimiento") or "").strip() or None,
            "codigo_verificacion": (payload.get("codigo_verificacion") or "").strip() or None,
            "fuente": "perudevs",
        }
