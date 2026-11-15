# -*- coding: utf-8 -*-
"""Balance de comprobación: sumas y saldos por cuenta, cuadre global."""
from __future__ import annotations

from .libro_mayor import mayor


def balance_comprobacion(repo, desde=None, hasta=None):
    """Suma de debe/haber por cuenta. Verifica cuadre global.

    Devuelve:
      {
        "cuentas": {cuenta: {debe, haber, saldo, movimientos}},
        "total_debe": int,
        "total_haber": int,
        "cuadra": bool,
      }
    """
    mayor_data = mayor(repo, desde, hasta)
    total_debe = sum(c["debe"] for c in mayor_data.values())
    total_haber = sum(c["haber"] for c in mayor_data.values())
    return {
        "cuentas": mayor_data,
        "total_debe": total_debe,
        "total_haber": total_haber,
        "cuadra": total_debe == total_haber,
    }
