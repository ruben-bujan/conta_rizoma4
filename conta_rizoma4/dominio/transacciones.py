"""Reglas conceptuales de transacciones append-only del dominio."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable


@dataclass(frozen=True)
class OperacionAppendOnly:
    tipo: str
    entidad_id: str
    objeto_tipo: str
    objeto_id: str
    actor_id: str
    timestamp: datetime
    motivo: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TransaccionAppendOnly:
    transaccion_id: str
    entidad_id: str
    operaciones: tuple[OperacionAppendOnly, ...]
    precondiciones: tuple[str, ...]
    motivo_global: str


def validar_transaccion_append_only(transaccion: TransaccionAppendOnly) -> None:
    """Validación mínima previa a una implementación PostgreSQL real."""
    if not transaccion.operaciones:
        raise ValueError("La transacción debe contener al menos una operación")
    if not transaccion.motivo_global:
        raise ValueError("La transacción requiere motivo global")

    entidades = {operacion.entidad_id for operacion in transaccion.operaciones}
    if entidades != {transaccion.entidad_id}:
        raise ValueError("La transacción contiene entidades distintas")

    for operacion in transaccion.operaciones:
        if not operacion.actor_id:
            raise ValueError("Toda operación requiere actor")
        if not operacion.motivo:
            raise ValueError("Toda operación requiere motivo")
