"""Compatibilidad progresiva entre la POC y el paquete formal del dominio."""
from __future__ import annotations

from typing import Any


def linea_poc_a_dominio(linea_poc: Any):
    """Convierte una línea mínima POC al modelo formal."""
    from .entidades.contables import Linea

    return Linea(
        cuenta=linea_poc.cuenta,
        debe=linea_poc.debe,
        haber=linea_poc.haber,
    )


def linea_dominio_a_poc(linea_dominio: Any):
    """Convierte una línea formal a una línea compatible con la POC."""
    from poc_epistemico_contable.modelo import Linea

    return Linea(
        cuenta=linea_dominio.cuenta,
        debe=linea_dominio.debe,
        haber=linea_dominio.haber,
    )
