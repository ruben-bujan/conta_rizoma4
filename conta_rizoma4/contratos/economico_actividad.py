# -*- coding: utf-8 -*-
"""A — Actividad (Nivel1..Nivel6, 927 filas, cargadas de Postgres).

La dimensión A del modelo A+B+C+D. Jerarquía de 6 niveles del PGC.
Las 927 filas están en la tabla `pgc_jerarquia` de Postgres.

Nivel1..Nivel6 son los 6 niveles de clasificación de la actividad:
  Nivel1: 77 filas
  Nivel2: 416 filas
  Nivel3: 397 filas
  Nivel4: 14 filas
  Nivel5: 12 filas
  Nivel6: 11 filas (cuentas operativas reales del cliente)

La relación padre-hijo se reconstruye en un paso posterior, leyendo
los campos `grupo` / `id_nivelN` de MariaDB (no están en el seed).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

import psycopg


PG_URL = os.environ.get(
    "CONTA_PG_URL",
    "postgresql://rizoma:rizoma_dev@localhost:5433/conta_rizoma4",
)

NIVELES = ("nivel1", "nivel2", "nivel3", "nivel4", "nivel5", "nivel6")


@dataclass
class Actividad:
    nivel: str
    id: int
    codigo: str
    nombre: str
    hijos: list["Actividad"] = field(default_factory=list)

    def __str__(self) -> str:
        return f"[{self.nivel}] {self.codigo} — {self.nombre}"


_cache: dict[str, dict[int, Actividad]] | None = None


def cargar_jerarquia_actividad(
    pg_url: Optional[str] = None,
) -> dict[str, dict[int, Actividad]]:
    """Carga los 6 niveles en {nivel: {id: Actividad}}.

    Cachea el resultado. Para invalidar, llama a
    `invalidar_cache_actividad()`.
    """
    global _cache
    if _cache is not None:
        return _cache
    url = pg_url or PG_URL
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT nivel, id, codigo, nombre FROM pgc_jerarquia "
                "ORDER BY nivel, id"
            )
            rows = cur.fetchall()
    _cache = {}
    for nivel, id_, codigo, nombre in rows:
        _cache.setdefault(nivel, {})[id_] = Actividad(
            nivel=nivel, id=id_, codigo=codigo, nombre=nombre,
        )
    return _cache


def invalidar_cache_actividad() -> None:
    global _cache
    _cache = None