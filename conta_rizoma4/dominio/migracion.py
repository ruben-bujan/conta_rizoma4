"""Modelo conceptual de migración del legado al dominio nuevo.

No ejecuta PostgreSQL ni modifica datos existentes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class CorrespondenciaHeredada:
    """Relación reversible entre un objeto heredado y una entidad nueva."""
    origen_tipo: str
    origen_empresa: str
    origen_indice: Optional[int]
    destino_tipo: str
    destino_id: str
    estado_migracion: str
    observaciones: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResultadoImportacion:
    objeto_tipo: str
    objeto_id: str
    creado: bool
    estado_epistemologico: str
    correspondencia: CorrespondenciaHeredada


def crear_correspondencia_asiento(
    empresa_id: str,
    indice: int,
    representacion_id: str,
    observaciones: tuple[str, ...] = (),
) -> CorrespondenciaHeredada:
    return CorrespondenciaHeredada(
        origen_tipo="ASIENTO_CONTABLE_HEREDADO",
        origen_empresa=empresa_id,
        origen_indice=indice,
        destino_tipo="REPRESENTACION_CONTABLE",
        destino_id=representacion_id,
        estado_migracion="IMPORTADO_SIN_ACREDITACION_EPSTEMICA",
        observaciones=observaciones,
    )
