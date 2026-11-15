# -*- coding: utf-8 -*-
"""Libro diario: listado de asientos con sus líneas."""
from __future__ import annotations


def listar_diario(repo, desde=None, hasta=None):
    """Lista asientos con sus líneas, ordenados por fecha."""
    headers = repo.listar(indice_desde=desde, indice_hasta=hasta, limite=100_000)
    resultado = []
    for h in headers:
        full = repo.obtener(h["indice"])
        resultado.append(full)
    return resultado


def totales_diario(asientos):
    """Totales de debe y haber del diario."""
    total_debe = sum(
        l["debe_centimos"] for a in asientos for l in a["lineas"]
    )
    total_haber = sum(
        l["haber_centimos"] for a in asientos for l in a["lineas"]
    )
    return {
        "n_asientos": len(asientos),
        "total_debe": total_debe,
        "total_haber": total_haber,
        "cuadra": total_debe == total_haber,
    }
