# -*- coding: utf-8 -*-
"""Helper unificado: crear cualquier acto por código."""
from __future__ import annotations

from .actos.catalogo import obtener


def crear_acto_por_codigo(codigo: str, **params):
    """Crea un Asiento a partir de un código del catálogo."""
    _, fn = obtener(codigo)
    return fn(**params)
