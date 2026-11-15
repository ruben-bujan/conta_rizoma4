# -*- coding: utf-8 -*-
"""Modelo de partida doble: Linea, Asiento, validación de cuadre."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional


class PartidaDobleError(Exception):
    """Error en la construcción o validación de un asiento."""


@dataclass(frozen=True)
class Linea:
    cuenta_pgc: str
    debe_centimos: int = 0
    haber_centimos: int = 0
    parrafo_pgc_id: Optional[int] = None
    concepto_linea: Optional[str] = None

    def __post_init__(self):
        if self.debe_centimos < 0 or self.haber_centimos < 0:
            raise PartidaDobleError(
                f"línea {self.cuenta_pgc}: importes negativos no permitidos"
            )
        if self.debe_centimos > 0 and self.haber_centimos > 0:
            raise PartidaDobleError(f"línea {self.cuenta_pgc}: debe y haber > 0")
        if self.debe_centimos == 0 and self.haber_centimos == 0:
            raise PartidaDobleError(f"línea {self.cuenta_pgc}: debe y haber = 0")

    @property
    def importe_centimos(self) -> int:
        return self.debe_centimos + self.haber_centimos

    def __str__(self) -> str:
        if self.debe_centimos > 0:
            return f"D {self.cuenta_pgc}: {self.debe_centimos}"
        return f"H {self.cuenta_pgc}: {self.haber_centimos}"


@dataclass(frozen=True)
class Asiento:
    indice: int
    fecha: date
    concepto: str
    lineas: tuple[Linea, ...]
    hash_previo: str
    hash: str
    huella_contenido: str
    metadatos: dict[str, Any] = field(default_factory=dict)

    @property
    def total_debe(self) -> int:
        return sum(l.debe_centimos for l in self.lineas)

    @property
    def total_haber(self) -> int:
        return sum(l.haber_centimos for l in self.lineas)

    @property
    def cuadra(self) -> bool:
        return self.total_debe == self.total_haber
