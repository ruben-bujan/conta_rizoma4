"""Servicios puros de diario, mayor y balance de comprobación."""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from ..entidades.contables import RepresentacionContable


def diario(representaciones: Iterable[RepresentacionContable]) -> list[RepresentacionContable]:
    return sorted(representaciones, key=lambda r: (r.fecha_contable, r.representacion_id))


def mayor(representaciones: Iterable[RepresentacionContable]) -> dict[str, dict]:
    cuentas: dict[str, dict] = defaultdict(lambda: {"debe": 0, "haber": 0, "saldo": 0, "movimientos": []})
    for representacion in representaciones:
        for linea in representacion.lineas:
            datos = cuentas[linea.cuenta]
            datos["debe"] += linea.debe
            datos["haber"] += linea.haber
            datos["movimientos"].append({
                "representacion_id": representacion.representacion_id,
                "fecha": representacion.fecha_contable,
                "debe": linea.debe,
                "haber": linea.haber,
            })

    for datos in cuentas.values():
        datos["saldo"] = datos["debe"] - datos["haber"]
    return dict(cuentas)


def balance_comprobacion(representaciones: Iterable[RepresentacionContable]) -> dict:
    mayor_data = mayor(representaciones)
    total_debe = sum(datos["debe"] for datos in mayor_data.values())
    total_haber = sum(datos["haber"] for datos in mayor_data.values())
    return {
        "cuentas": mayor_data,
        "total_debe": total_debe,
        "total_haber": total_haber,
        "cuadra": total_debe == total_haber,
    }
