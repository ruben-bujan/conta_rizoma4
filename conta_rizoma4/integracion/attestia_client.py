# -*- coding: utf-8 -*-
"""Cliente de conta-rizoma4 hacia attestia."""
from __future__ import annotations

import os
import requests

ATTESTIA_URL = os.environ.get("ATTESTIA_URL", "http://localhost:8002")


class AttestiaClient:
    def __init__(self, base_url: str = ATTESTIA_URL):
        self.base = base_url.rstrip("/")

    def generar_claves(self):
        return requests.post(f"{self.base}/claves").json()

    def firmar(self, datos: str):
        return requests.post(f"{self.base}/firmar", json={"datos": datos}).json()

    def verificar(self, datos: str, firma_hex: str):
        return requests.post(f"{self.base}/verificar", json={"datos": datos, "firma_hex": firma_hex}).json()
