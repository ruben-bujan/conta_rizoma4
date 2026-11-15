# -*- coding: utf-8 -*-
"""Primitivas de la cadena de asientos.

  - GENESIS: hash previo del primer asiento ("0" * 64)
  - calcular_huella(contenido): sha256 del contenido canónico
  - calcular_hash(huella, hash_previo, indice): sha256 encadenado

Formato del hash: sha256(f"{hash_previo}|{huella}|{indice}")
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


GENESIS = "0" * 64


def calcular_huella(contenido: dict[str, Any]) -> str:
    """sha256 del contenido canónico (JSON ordenado, sin espacios)."""
    payload = json.dumps(
        contenido, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def calcular_hash(huella: str, hash_previo: str, indice: int) -> str:
    """sha256 encadenado. GENESIS para el primer asiento."""
    if not hash_previo:
        raise ValueError("hash_previo vacío: usa GENESIS para el primero")
    if indice < 0:
        raise ValueError(f"indice inválido: {indice}")
    payload = f"{hash_previo}|{huella}|{indice}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()