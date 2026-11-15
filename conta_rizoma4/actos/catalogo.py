# -*- coding: utf-8 -*-
"""Catálogo unificado de los 51 actos económicos."""
from __future__ import annotations

from . import (
    facturacion, fiscal, cierre, inmovilizado,
    existencias, societarias, ajustes,
)


# Mapa: {codigo: (modulo, funcion)}
_GRUPOS = {
    "facturacion": facturacion.ACTOS,
    "fiscal": fiscal.ACTOS,
    "cierre": cierre.ACTOS,
    "inmovilizado": inmovilizado.ACTOS,
    "existencias": existencias.ACTOS,
    "societarias": societarias.ACTOS,
    "ajustes": ajustes.ACTOS,
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
    """Devuelve (grupo, funcion) o levanta ValueError."""
    if codigo not in CATALOGO:
        raise ValueError(
            f"Acto desconocido: {codigo}. "
            f"Disponibles ({len(CATALOGO)}): {sorted(CATALOGO.keys())}"
        )
    return CATALOGO[codigo]


def contar() -> int:
    return len(CATALOGO)
