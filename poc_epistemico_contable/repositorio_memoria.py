"""Adaptador en memoria de los puertos del núcleo POC."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from .nucleo import NucleoEpistemicoContable
from .puertos import RepositorioDominio


class RepositorioMemoria(RepositorioDominio):
    def __init__(self, nucleo: NucleoEpistemicoContable) -> None:
        self.nucleo = nucleo
        self._objetos: dict[tuple[str, str], Any] = {}

    def guardar(self, tipo: str, identidad: str, objeto: Any) -> None:
        self._objetos[(tipo, identidad)] = objeto

    def obtener(self, tipo: str, identidad: str) -> Optional[Any]:
        return self._objetos.get((tipo, identidad))

    def reconstruir(self, fecha_epistemica: datetime) -> dict[str, Any]:
        return self.nucleo.reconstruir(fecha_epistemica)
