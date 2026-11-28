# -*- coding: utf-8 -*-
"""Libro mayor: saldos por cuenta con soporte de filtros por fecha."""
from __future__ import annotations
from datetime import date
from typing import Optional


def mayor(
    repo, 
    desde: Optional[int] = None, 
    hasta: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
):
    """Saldos por cuenta filtrados por índice o fecha: {cuenta: {debe, haber, saldo, movimientos}}."""
    try:
        headers = repo.listar(
            indice_desde=desde, 
            indice_hasta=hasta, 
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            limite=100_000
        )
    except TypeError:
        headers = repo.listar(indice_desde=desde, indice_hasta=hasta, limite=100_000)

    cuentas = {}
    for a in headers:
        full = repo.obtener(a["indice"])
        if not full:
            continue
        
        # Filtro de seguridad por fecha en memoria
        f_asiento = full.get("fecha")
        if fecha_desde and f_asiento < fecha_desde:
            continue
        if fecha_hasta and f_asiento > fecha_hasta:
            continue

        for l in full["lineas"]:
            c = l["cuenta_pgc"]
            if c not in cuentas:
                cuentas[c] = {"debe": 0, "haber": 0, "saldo": 0, "movimientos": []}
            cuentas[c]["debe"] += l["debe_centimos"]
            cuentas[c]["haber"] += l["haber_centimos"]
            cuentas[c]["movimientos"].append({
                "asiento": full["indice"],
                "fecha": full["fecha"],
                "debe": l["debe_centimos"],
                "haber": l["haber_centimos"],
                "concepto": full["concepto"],
                "concepto_linea": l.get("concepto_linea"),
            })

    for c in cuentas.values():
        c["saldo"] = c["debe"] - c["haber"]
    return cuentas


def saldo_cuenta(
    repo, 
    cuenta: str, 
    desde: Optional[int] = None, 
    hasta: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
):
    """Saldo de una cuenta concreta con soporte de fechas."""
    mayor_data = mayor(repo, desde=desde, hasta=hasta, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
    if cuenta not in mayor_data:
        return {"cuenta": cuenta, "debe": 0, "haber": 0, "saldo": 0, "movimientos": []}
    return {"cuenta": cuenta, **mayor_data[cuenta]}
