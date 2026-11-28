"""Modelos mínimos de integración extraordinaria con RIZOMA4.

Este módulo no realiza llamadas HTTP. Es el contrato local que deberá ser
implementado por adaptadores externos.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass(frozen=True)
class VinculoRizoma4:
    entidad_contable_id: str
    hecho_id: Optional[str]
    caso_rizoma4_id: str
    creado_en: datetime
    activo: bool = True


@dataclass(frozen=True)
class HipotesisRizoma4:
    hipotesis_id: str
    caso_id: str
    contenido: str
    recibida_en: datetime
    version_contrato: str
    evidencias: tuple[str, ...] = ()
    metadatos: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AlertaRizoma4:
    alerta_id: str
    caso_id: str
    objeto_id: str
    descripcion: str
    recibida_en: datetime
    version_contrato: str


def validar_vinculo(vinculo: VinculoRizoma4) -> None:
    if not vinculo.entidad_contable_id:
        raise ValueError("entidad_contable_id es obligatorio")
    if not vinculo.caso_rizoma4_id:
        raise ValueError("caso_rizoma4_id es obligatorio")
