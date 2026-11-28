# -*- coding: utf-8 -*-
"""Balance de comprobación: sumas y saldos por cuenta, cuadre global con soporte de fechas."""
from __future__ import annotations

from datetime import date
from typing import Optional
from .libro_mayor import mayor


def balance_comprobacion(
    repo, 
    desde: Optional[int] = None, 
    hasta: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
):
    """Suma de debe/haber por cuenta. Verifica cuadre global (con soporte de fechas)."""
    mayor_data = mayor(repo, desde=desde, hasta=hasta, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
    total_debe = sum(c["debe"] for c in mayor_data.values())
    total_haber = sum(c["haber"] for c in mayor_data.values())
    return {
        "cuentas": mayor_data,
        "total_debe": total_debe,
        "total_haber": total_haber,
        "cuadra": total_debe == total_haber,
    }