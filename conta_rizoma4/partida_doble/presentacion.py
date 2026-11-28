# -*- coding: utf-8 -*-
"""Presentación formateada del balance y PyG por grupos PGC con soporte de fechas (H-09)."""
from __future__ import annotations

from datetime import date
from typing import Optional
from .libro_mayor import mayor


_GRUPOS_ACTIVO = {
    1: "Financiación básica",
    2: "Inmovilizado",
    3: "Existencias",
    4: "Acreedores y deudores",
    5: "Cuentas financieras",
}

_GRUPOS_PYG = {
    6: "Compras y gastos",
    7: "Ventas e ingresos",
}

# Cuentas correctoras del activo (mismo criterio que cuentas_anuales)
_CORRECTORES_ACTIVO = ("28", "29", "39", "49", "59")


def _es_corrector(cuenta: str) -> bool:
    return any(cuenta.startswith(p) for p in _CORRECTORES_ACTIVO)


def balance_formateado(
    repo, 
    desde: Optional[int] = None, 
    hasta: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
):
    """Balance agrupado por grupos 1-5 del PGC con soporte de fechas."""
    mayor_data = mayor(repo, desde=desde, hasta=hasta, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
    activo = {1: {}, 2: {}, 3: {}, 4: {}, 5: {}}
    pasivo = {1: {}, 2: {}, 3: {}, 4: {}, 5: {}}
    correctores = {}
    gastos_total = 0
    ingresos_total = 0

    for cuenta, datos in mayor_data.items():
        if not cuenta or not cuenta[0].isdigit():
            continue
        grupo = int(cuenta[0])
        saldo = datos["saldo"]
        if saldo == 0:
            continue
        if grupo in (1, 2, 3, 4, 5):
            if _es_corrector(cuenta):
                correctores[cuenta] = abs(saldo)
            elif saldo > 0:
                activo[grupo][cuenta] = saldo
            else:
                pasivo[grupo][cuenta] = -saldo
        elif grupo == 6:
            gastos_total += saldo
        elif grupo == 7:
            ingresos_total += -saldo

    resultado = ingresos_total - gastos_total
    total_activo = (
        sum(sum(g.values()) for g in activo.values())
        - sum(correctores.values())
    )
    total_pasivo = sum(sum(g.values()) for g in pasivo.values())

    return {
        "activo": activo,
        "pasivo": pasivo,
        "correctores": correctores,
        "resultado_ejercicio": resultado,
        "total_activo": total_activo,
        "total_pasivo": total_pasivo,
        "total_pasivo_mas_resultado": total_pasivo + resultado,
        "cuadra": total_activo == total_pasivo + resultado,
    }


def pyg_formateado(
    repo, 
    desde: Optional[int] = None, 
    hasta: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
):
    """PyG agrupada por grupos 6-7 del PGC con soporte de fechas."""
    mayor_data = mayor(repo, desde=desde, hasta=hasta, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
    gastos = {}
    ingresos = {}
    for cuenta, datos in mayor_data.items():
        if not cuenta or not cuenta[0].isdigit():
            continue
        grupo = int(cuenta[0])
        saldo = datos["saldo"]
        if saldo == 0:
            continue
        if grupo == 6:
            gastos[cuenta] = saldo
        elif grupo == 7:
            ingresos[cuenta] = -saldo
    return {
        "gastos": gastos,
        "ingresos": ingresos,
        "total_gastos": sum(gastos.values()),
        "total_ingresos": sum(ingresos.values()),
        "resultado": sum(ingresos.values()) - sum(gastos.values()),
    }