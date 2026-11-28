"""Diseño exclusivo de repositorio PostgreSQL de escritura.

No contiene conexión ni ejecución SQL. Debe servir para especificar contratos,
transacciones y verificaciones antes de implementar un adaptador real.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Iterable, Optional


class OperacionEscritura:
    def __init__(
        self,
        tipo: str,
        entidad_id: str,
        objeto_id: str,
        payload: dict[str, Any],
        actor_id: str,
        motivo: str,
        timestamp: datetime,
    ) -> None:
        self.tipo = tipo
        self.entidad_id = entidad_id
        self.objeto_id = objeto_id
        self.payload = payload
        self.actor_id = actor_id
        self.motivo = motivo
        self.timestamp = timestamp


class TransaccionDominio(ABC):
    @abstractmethod
    def registrar_hecho(self, entidad_id: str, objeto: Any, evento: Any) -> None:
        pass

    @abstractmethod
    def registrar_evidencia(self, entidad_id: str, objeto: Any, evento: Any) -> None:
        pass

    @abstractmethod
    def registrar_interpretacion(self, entidad_id: str, objeto: Any, evento: Any) -> None:
        pass

    @abstractmethod
    def registrar_decision(self, entidad_id: str, objeto: Any, evento: Any) -> None:
        pass

    @abstractmethod
    def registrar_representacion(self, entidad_id: str, objeto: Any, evento: Any) -> None:
        pass

    @abstractmethod
    def registrar_rectificacion(self, entidad_id: str, objeto: Any, evento: Any) -> None:
        pass


class RepositorioEscrituraPostgresDiseno(ABC):
    """Contrato futuro: una operación productiva debe confirmar todo o nada."""

    @abstractmethod
    def ejecutar_transaccion(
        self,
        operaciones: Iterable[OperacionEscritura],
        verificar_integridad_previa: bool = True,
    ) -> None:
        pass

    @abstractmethod
    def verificar_append_only(self, entidad_id: str) -> bool:
        pass

    @abstractmethod
    def crear_reconciliacion(
        self,
        entidad_id: str,
        fecha_corte: datetime,
        motivo: str,
    ) -> dict[str, Any]:
        pass

    @abstractmethod
    def rollback_transaccion(
        self,
        entidad_id: str,
        transaccion_id: str,
        motivo: str,
    ) -> None:
        pass
