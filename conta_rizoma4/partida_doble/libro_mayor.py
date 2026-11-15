# -*- coding: utf-8 -*-
"""Libro mayor: saldos por cuenta."""
from __future__ import annotations


def mayor(repo, desde=None, hasta=None):
    """Saldos por cuenta: {cuenta: {debe, haber, saldo, movimientos}}."""
    asientos = repo.listar(indice_desde=desde, indice_hasta=hasta, limite=100_000)
    cuentas = {}
    for a in asientos:
        full = repo.obtener(a["indice"])
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


def saldo_cuenta(repo, cuenta, desde=None, hasta=None):
    """Saldo de una cuenta concreta."""
    mayor_data = mayor(repo, desde, hasta)
    if cuenta not in mayor_data:
        return {"cuenta": cuenta, "debe": 0, "haber": 0, "saldo": 0, "movimientos": []}
    return {"cuenta": cuenta, **mayor_data[cuenta]}
