"""Modelo conceptual mínimo de la POC, independiente de infraestructura."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Iterable, Optional


class EstadoEpistemologico(str, Enum):
    NO_ACREDITADO = "NO_ACREDITADO"
    DECLARADO = "DECLARADO"
    CONTRASTADO_PARCIALMENTE = "CONTRASTADO_PARCIALMENTE"
    ACREDITADO = "ACREDITADO"
    CONTRADICHO = "CONTRADICHO"
    RECTIFICADO = "RECTIFICADO"
    RECHAZADO = "RECHAZADO"


class EstadoInterpretacion(str, Enum):
    PROPUESTA = "PROPUESTA"
    EVALUADA = "EVALUADA"
    ADOPTADA = "ADOPTADA"
    DESCARTADA = "DESCARTADA"
    REVOCADA = "REVOCADA"


class EstadoDecision(str, Enum):
    PROPUESTA = "PROPUESTA"
    APROBADA = "APROBADA"
    ADOPTADA = "ADOPTADA"
    EJECUTADA = "EJECUTADA"
    REVOCADA = "REVOCADA"


class EstadoRepresentacion(str, Enum):
    PROPUESTA = "PROPUESTA"
    VALIDADA = "VALIDADA"
    REGISTRADA = "REGISTRADA"
    RECTIFICADA = "RECTIFICADA"


class TipoFecha(str, Enum):
    EXACTA = "EXACTA"
    ESTIMADA = "ESTIMADA"
    RANGO = "RANGO"
    DESCONOCIDA = "DESCONOCIDA"


@dataclass(frozen=True)
class FechaEconomica:
    tipo: TipoFecha
    inicio: Optional[datetime] = None
    fin: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.tipo == TipoFecha.EXACTA and self.inicio is None:
            raise ValueError("Una fecha exacta requiere inicio")
        if self.tipo == TipoFecha.RANGO and (self.inicio is None or self.fin is None):
            raise ValueError("Una fecha de rango requiere inicio y fin")


@dataclass(frozen=True)
class Magnitud:
    tipo: str
    importe: int
    moneda: str = "EUR"
    incertidumbre: Optional[str] = None

    def __post_init__(self) -> None:
        if self.importe < 0:
            raise ValueError("La magnitud no puede ser negativa")


@dataclass(frozen=True)
class Incertidumbre:
    tipo: str
    descripcion: str
    minima: Optional[int] = None
    maxima: Optional[int] = None


@dataclass
class EntidadContable:
    entidad_id: str
    nombre: str
    moneda: str = "EUR"


@dataclass
class ParteEconomica:
    parte_id: str
    entidad_id: str
    rol: str


@dataclass
class HechoEconomico:
    hecho_id: str
    entidad_id: str
    tipo: str
    descripcion: str
    ocurrido: FechaEconomica
    conocido_en: datetime
    registrado_en: datetime
    estado_economico: str
    estado_epistemologico: EstadoEpistemologico = EstadoEpistemologico.NO_ACREDITADO
    partes: tuple[ParteEconomica, ...] = ()
    incertidumbre: Optional[Incertidumbre] = None
    magnitudes: tuple[Magnitud, ...] = ()
    relaciones: dict[str, str] = field(default_factory=dict)


@dataclass
class Fuente:
    fuente_id: str
    tipo: str
    identidad: str
    competencia: Optional[str] = None


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
    vigente_hasta: Optional[datetime] = None


@dataclass
class Interpretacion:
    interpretacion_id: str
    hecho_id: str
    tipo: str
    descripcion: str
    evidencia_ids: tuple[str, ...]
    criterio_ids: tuple[str, ...]
    incertidumbre: Optional[Incertidumbre]
    propuesta_por: str
    propuesta_en: datetime
    estado: EstadoInterpretacion = EstadoInterpretacion.PROPUESTA


@dataclass
class Actor:
    actor_id: str
    nombre: str
    tipo: str = "HUMANO"


@dataclass
class Autorizacion:
    autorizacion_id: str
    actor_id: str
    competencia: str
    alcance: str
    otorgada_en: datetime


@dataclass
class Decision:
    decision_id: str
    objeto_id: str
    interpretacion_adoptada_id: str
    interpretaciones_descartadas: tuple[str, ...]
    criterio_ids: tuple[str, ...]
    evidencia_ids: tuple[str, ...]
    motivo: str
    actor_id: str
    autorizacion_id: Optional[str]
    decidida_en: datetime
    estado: EstadoDecision = EstadoDecision.PROPUESTA


@dataclass(frozen=True)
class Linea:
    cuenta: str
    debe: int = 0
    haber: int = 0

    def __post_init__(self) -> None:
        if self.debe < 0 or self.haber < 0:
            raise ValueError("Los importes no pueden ser negativos")
        if self.debe > 0 and self.haber > 0:
            raise ValueError("Una línea no puede tener debe y haber")


@dataclass
class RepresentacionContable:
    representacion_id: str
    hecho_ids: tuple[str, ...]
    interpretacion_id: str
    decision_id: str
    criterio_ids: tuple[str, ...]
    marco: str
    fecha_contable: datetime
    lineas: tuple[Linea, ...]
    estado: EstadoRepresentacion = EstadoRepresentacion.PROPUESTA

    def cuadra(self) -> bool:
        return sum(l.debe for l in self.lineas) == sum(l.haber for l in self.lineas)


@dataclass
class Rectificacion:
    rectificacion_id: str
    representacion_original_id: str
    representacion_nueva_id: str
    tipo: str
    causa: str
    motivo: str
    actor_id: str
    autorizacion_id: Optional[str]
    creada_en: datetime


@dataclass
class Evento:
    evento_id: str
    tipo: str
    objeto_id: str
    actor_id: str
    timestamp: datetime
    estado_anterior: Optional[Any]
    estado_posterior: Optional[Any]
    motivo: str
    referencia_ids: tuple[str, ...] = ()
    payload: dict[str, Any] = field(default_factory=dict)
