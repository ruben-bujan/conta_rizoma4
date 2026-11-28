"""Puerto abstracto de persistencia del dominio."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional


class RepositorioDominio(ABC):
    @abstractmethod
    def guardar(self, tipo: str, identidad: str, objeto: Any) -> None:
        pass

    @abstractmethod
    def obtener(self, tipo: str, identidad: str) -> Optional[Any]:
        pass

    @abstractmethod
    def reconstruir(self, fecha_epistemica: datetime) -> dict[str, Any]:
        pass
