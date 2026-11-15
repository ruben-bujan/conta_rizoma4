# -*- coding: utf-8 -*-
"""Modelo de consolidación de grupo clásico."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


class ConsolidacionError(Exception):
    """Error en el proceso de consolidación."""


@dataclass(frozen=True)
class RelacionGrupo:
    matriz_id: str
    filial_id: str
    porcentaje: float
    fecha_inicio: date
    fecha_fin: Optional[date] = None

    def __post_init__(self):
        if not (0 < self.porcentaje <= 100):
            raise ConsolidacionError(
                f"porcentaje fuera de (0,100]: {self.porcentaje}"
            )


@dataclass(frozen=True)
class EliminacionPropuesta:
    empresa_a: str
    empresa_b: str
    cuenta_a: str
    cuenta_b: str
    importe_centimos: int
    motivo: str  # 'venta_intragrupo' | 'prestamo_intragrupo' | 'dividendo'


@dataclass
class BalanceConsolidado:
    grupo_id: str
    fecha_cierre: date
    empresas_incluidas: list[str]
    activo: dict[str, dict[str, int]] = field(default_factory=dict)
    pasivo: dict[str, dict[str, int]] = field(default_factory=dict)
    resultado_grupo: int = 0
    resultado_atribuible_matriz: int = 0
    resultado_atribuible_minoritarios: int = 0
    eliminaciones_aplicadas: list[EliminacionPropuesta] = field(default_factory=list)
    cuadra: bool = False
