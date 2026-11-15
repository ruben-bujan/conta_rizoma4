# -*- coding: utf-8 -*-
"""B — Interlocutor (PersonaFisica / PersonaJuridica)."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TipoPersona(str, Enum):
    FISICA = "FISICA"
    JURIDICA = "JURIDICA"


@dataclass
class Interlocutor:
    tipo: TipoPersona
    nombre: str
    nif: Optional[str] = None
    domicilio: Optional[str] = None
    cp: Optional[str] = None
    ciudad: Optional[str] = None
    pais: str = "ES"

    def __str__(self) -> str:
        return f"[{self.tipo.value}] {self.nombre} (NIF={self.nif or '?'})"


@dataclass
class PersonaFisica(Interlocutor):
    tipo: TipoPersona = field(default=TipoPersona.FISICA, init=False)


@dataclass
class PersonaJuridica(Interlocutor):
    tipo: TipoPersona = field(default=TipoPersona.JURIDICA, init=False)
    razon_social: Optional[str] = None
    cnae: Optional[str] = None