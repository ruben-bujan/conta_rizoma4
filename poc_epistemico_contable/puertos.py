"""Puertos abstractos de infraestructura para el núcleo POC."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional


class RepositorioDominio(ABC):
    """Puerto para almacenar y reconstruir objetos del dominio."""

    @abstractmethod
    def guardar(self, tipo: str, identidad: str, objeto: Any) -> None:
        pass

    @abstractmethod
    def obtener(self, tipo: str, identidad: str) -> Optional[Any]:
        pass

    @abstractmethod
    def reconstruir(self, fecha_epistemica: datetime) -> dict[str, Any]:
        pass


class ServicioReloj(ABC):
    @abstractmethod
    def ahora(self) -> datetime:
        pass


class ServicioIdentidad(ABC):
    @abstractmethod
    def resolver_actor(self, identificador: str) -> Any:
        pass


class ServicioCustodia(ABC):
    @abstractmethod
    def verificar_integridad(self, referencia: str, hash_esperado: str) -> bool:
        pass


class ServicioIntegracionExterna(ABC):
    """Puerto opcional para fuentes extraordinarias como RIZOMA4."""

    @abstractmethod
    def consultar(self, operacion: str, parametros: dict[str, Any]) -> Any:
        pass
