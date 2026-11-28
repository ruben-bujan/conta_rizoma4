"""Servicios puros de vencimientos y antigüedad de deuda."""
from __future__ import annotations

from datetime import datetime

from ..entidades.economicas import Vencimiento


def dias_vencido(vencimiento: Vencimiento, fecha_corte: datetime) -> int:
    if vencimiento.fecha_vencimiento is None:
        return 0
    diferencia = (fecha_corte.date() - vencimiento.fecha_vencimiento.date()).days
    return max(0, diferencia)


def antiguedad_vencimiento(vencimiento: Vencimiento, fecha_corte: datetime) -> str:
    dias = dias_vencido(vencimiento, fecha_corte)
    if dias == 0:
        return "NO_VENCIDO"
    if dias <= 30:
        return "1_30_DIAS"
    if dias <= 60:
        return "31_60_DIAS"
    if dias <= 90:
        return "61_90_DIAS"
    return "MAS_90_DIAS"
