# -*- coding: utf-8 -*-
"""Libro diario: listado de asientos con sus líneas y soporte de filtros por fecha."""
from __future__ import annotations
from datetime import date
from typing import Optional


def listar_diario(
    repo, 
    desde: Optional[int] = None, 
    hasta: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
):
    """Lista asientos con sus líneas, ordenados por fecha y índice."""
    # Si el repositorio soporta filtros de fecha directamente, los pasamos; 
    # de lo contrario, obtenemos el rango por índice y filtramos en memoria.
    try:
        headers = repo.listar(
            indice_desde=desde, 
            indice_hasta=hasta, 
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            limite=100_000
        )
    except TypeError:
        # Fallback si el repositorio antiguo solo acepta parámetros por índice
        headers = repo.listar(indice_desde=desde, indice_hasta=hasta, limite=100_000)

    resultado = []
    for h in headers:
        full = repo.obtener(h["indice"])
        if full:
            # Filtrado adicional por fecha si el repositorio no lo aplicó nativamente
            f_asiento = full.get("fecha")
            if fecha_desde and f_asiento < fecha_desde:
                continue
            if fecha_hasta and f_asiento > fecha_hasta:
                continue
            resultado.append(full)

    # Orden riguroso por fecha y después por índice para garantizar el rigor del diario (H-09)
    resultado.sort(key=lambda x: (x["fecha"], x["indice"]))
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