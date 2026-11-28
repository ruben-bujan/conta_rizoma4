"""Entidades epistemológicas mínimas promovidas desde la POC."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class EstadoInterpretacion(str, Enum):
    PROPUESTA = "PROPUESTA"
    EVALUADA = "EVALUADA"
    ADOPTADA = "ADOPTADA"
    DESCARTADA = "DESCARTADA"
    REVOCADA = "REVOCADA"


@dataclass
class Fuente:
    fuente_id: str
    tipo: str
    identidad: str
    competencia: str | None = None


@dataclass
class Evidencia:
    evidencia_id: str
    fuente_id: str
    tipo: str
    referencia: str
    recibida_en: datetime
    integridad: str = "NO_VERIFICADA"
    autenticidad: str = "NO_VALORADA"
    veracidad: str = "NO_VALORADA"
    calidad: str = "NO_VALORADA"
    registrada_en: datetime | None = None


@dataclass
class ValoracionEvidencia:
    evidencia_id: str
    hecho_id: str
    relacion: str
    integridad: str
    autenticidad: str
    veracidad: str
    fundamento: str
    valorado_en: datetime


@dataclass
class Criterio:
    criterio_id: str
    categoria: str
    nombre: str
    fundamento: str
    version: str
    vigente_desde: datetime
    vigente_hasta: datetime | None = None
    registrado_en: datetime | None = None


@dataclass
class Interpretacion:
    interpretacion_id: str
    hecho_id: str
    tipo: str
    descripcion: str
    evidencia_ids: tuple[str, ...]
    criterio_ids: tuple[str, ...]
    incertidumbre: object | None
    propuesta_por: str
    propuesta_en: datetime
    estado: EstadoInterpretacion = EstadoInterpretacion.PROPUESTA
