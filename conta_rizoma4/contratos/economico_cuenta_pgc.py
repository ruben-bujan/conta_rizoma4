# -*- coding: utf-8 -*-
"""D — Cuenta PGC (905 cuentas válidas, cargadas de Postgres)."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Optional

import psycopg


from ..config.postgresql import PG_URL

_SOLO_DIGITOS = re.compile(r"^\d+$")
_HEADER_SECCION = re.compile(r"^\d+\.\s")


@dataclass(frozen=True)
class CuentaPGC:
    id: int
    grupo: int
    cuenta: str
    descripcion: str

    @property
    def nivel(self) -> int:
        return len(self.cuenta)

    def __str__(self) -> str:
        return f"{self.cuenta} — {self.descripcion}"


_cache: dict[str, CuentaPGC] | None = None


def _es_cuenta_valida(cuenta: str, descripcion: str = "") -> bool:
    """Una cuenta PGC real: código solo dígitos (2-5), y la descripción
    no es un header de sección tipo '23. INMOVILIZACIONES...'."""
    if not _SOLO_DIGITOS.match(cuenta):
        return False
    if _HEADER_SECCION.match(descripcion):
        return False
    return True


def cargar_cuentas_pgc(pg_url: Optional[str] = None) -> dict[str, CuentaPGC]:
    """905 cuentas únicas por código (primera válida gana)."""
    global _cache
    if _cache is not None:
        return _cache
    url = pg_url or PG_URL
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, grupo, cuenta, descripcion FROM pgc_cuenta "
                "ORDER BY id"
            )
            rows = cur.fetchall()
    _cache = {}
    for id_, grupo, cuenta, desc in rows:
        if not _es_cuenta_valida(cuenta, desc):
            continue
        if cuenta not in _cache:
            _cache[cuenta] = CuentaPGC(
                id=id_, grupo=grupo, cuenta=cuenta, descripcion=desc,
            )
    return _cache


def cargar_todas_las_cuentas_pgc(
    pg_url: Optional[str] = None,
) -> list[CuentaPGC]:
    """905 filas de cuentas válidas (sin headers de sección)."""
    url = pg_url or PG_URL
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, grupo, cuenta, descripcion FROM pgc_cuenta "
                "ORDER BY id"
            )
            rows = cur.fetchall()
    return [
        CuentaPGC(id=id_, grupo=grupo, cuenta=cuenta, descripcion=desc)
        for id_, grupo, cuenta, desc in rows
        if _es_cuenta_valida(cuenta, desc)
    ]


def invalidar_cache_cuentas() -> None:
    global _cache
    _cache = None
