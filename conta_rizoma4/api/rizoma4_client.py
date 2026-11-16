# -*- coding: utf-8 -*-
"""Cliente HTTP mínimo a rizoma4 para el CAS de documentos."""
from __future__ import annotations

import os
from typing import Optional

import httpx


DEFAULT_URL = os.environ.get("RIZOMA4_API_URL", "http://localhost:8000")


class Rizoma4Error(Exception):
    pass


class ClienteRizoma4:
    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        self._base_url = (base_url or DEFAULT_URL).rstrip("/")
        self._timeout = timeout

    def _client(self) -> httpx.Client:
        return httpx.Client(timeout=self._timeout)

    def guardar_documento(self, empresa_id: str, contenido: bytes, nombre: str = "") -> dict:
        """Guarda un documento en el CAS de rizoma4. Devuelve {hash_cas}."""
        with self._client() as c:
            r = c.post(
                f"{self._base_url}/cas/subir",
                data={"empresa_id": empresa_id, "nombre": nombre},
                files={"contenido": ("doc", contenido)},
            )
            r.raise_for_status()
            return r.json()
