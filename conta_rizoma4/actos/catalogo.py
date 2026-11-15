# -*- coding: utf-8 -*-
"""Catálogo unificado de todos los actos económicos."""
from __future__ import annotations

from . import (
    facturacion, facturacion_avanzada,
    fiscal, fiscal_avanzado,
    cierre,
    inmovilizado, inmovilizado_avanzado,
    existencias, existencias_avanzado,
    societarias, societarias_avanzado,
    ajustes, ajustes_avanzado,
)


_GRUPOS = {
    "facturacion": facturacion.ACTOS,
    "facturacion_avanzada": facturacion_avanzada.ACTOS,
    "fiscal": fiscal.ACTOS,
    "fiscal_avanzado": fiscal_avanzado.ACTOS,
    "cierre": cierre.ACTOS,
    "inmovilizado": inmovilizado.ACTOS,
    "inmovilizado_avanzado": inmovilizado_avanzado.ACTOS,
    "existencias": existencias.ACTOS,
    "existencias_avanzado": existencias_avanzado.ACTOS,
    "societarias": societarias.ACTOS,
    "societarias_avanzado": societarias_avanzado.ACTOS,
    "ajustes": ajustes.ACTOS,
    "ajustes_avanzado": ajustes_avanzado.ACTOS,
}


def _todo() -> dict:
    todos = {}
    for grupo, actos in _GRUPOS.items():
        for codigo, fn in actos.items():
            todos[codigo] = (grupo, fn)
    return todos


CATALOGO = _todo()


def listar_grupos() -> list[str]:
    return sorted(_GRUPOS.keys())


def listar_por_grupo(grupo: str) -> list[str]:
    if grupo not in _GRUPOS:
        raise ValueError(f"Grupo desconocido: {grupo}")
    return sorted(_GRUPOS[grupo].keys())


def obtener(codigo: str):
    if codigo not in CATALOGO:
        raise ValueError(
            f"Acto desconocido: {codigo}. "
            f"Disponibles ({len(CATALOGO)}): {sorted(CATALOGO.keys())}"
        )
    return CATALOGO[codigo]


def contar() -> int:
    return len(CATALOGO)
