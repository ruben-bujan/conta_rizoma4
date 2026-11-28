# -*- coding: utf-8 -*-
"""Cliente HTTP de CONTA hacia la API de RIZOMA4."""
from __future__ import annotations

import os
from typing import Any, Optional

import requests

RIZOMA4_URL = os.getenv("RIZOMA4_URL", "http://localhost:8000")
RIZOMA4_API_TOKEN = os.getenv("RIZOMA4_API_TOKEN", "")


class Rizoma4Error(RuntimeError):
    """Error de comunicación o contrato con RIZOMA4."""


class ClienteRizoma4:
    def __init__(
        self,
        base_url: str = RIZOMA4_URL,
        token: Optional[str] = None,
        timeout: float = 15.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.token = RIZOMA4_API_TOKEN if token is None else token
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def listar_casos(self) -> list[dict[str, Any]]:
        """Devuelve los casos que la credencial de integración puede consultar."""
        try:
            response = requests.get(
                f"{self.base_url}/casos",
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            raise Rizoma4Error(f"No se pudo consultar RIZOMA4: {exc}") from exc
        except ValueError as exc:
            raise Rizoma4Error("RIZOMA4 devolvió una respuesta JSON inválida") from exc

        casos = payload.get("casos") if isinstance(payload, dict) else payload
        if not isinstance(casos, list):
            raise Rizoma4Error("Respuesta de GET /casos incompatible: se esperaba una lista 'casos'")
        return [c for c in casos if isinstance(c, dict) and c.get("caso_id")]

    def guardar_documento(
        self,
        empresa_id: str,
        contenido: bytes,
        nombre: str,
        caso_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Guarda el binario en CAS; si se indica caso_id usa el endpoint contextual."""
        if not contenido:
            raise Rizoma4Error("El documento está vacío")
        if caso_id:
            endpoint = f"{self.base_url}/casos/{caso_id}/ficheros"
            field_name = "fichero"
            data = {}
        else:
            endpoint = f"{self.base_url}/cas/subir"
            field_name = "contenido"
            data = {"empresa_id": empresa_id, "nombre": nombre}
        try:
            response = requests.post(
                endpoint,
                headers=self._headers(),
                data=data,
                files={field_name: (nombre or "documento", contenido)},
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            raise Rizoma4Error(f"No se pudo guardar el documento en CAS de RIZOMA4: {exc}") from exc
        except ValueError as exc:
            raise Rizoma4Error("RIZOMA4 devolvió una respuesta JSON inválida al subir el documento") from exc
        if not isinstance(payload, dict):
            raise Rizoma4Error("Respuesta de subida CAS incompatible")
        return payload
