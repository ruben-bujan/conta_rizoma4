"""Entidades contables y de trazabilidad para el núcleo nuevo."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class Rol(str, Enum):
    DIRECTOR = "DIRECTOR"
    SUBDIRECTOR = "SUBDIRECTOR"
    JEFE_CONTABILIDAD = "JEFE_CONTABILIDAD"
    OPERARIO = "OPERARIO"
    AUXILIAR = "AUXILIAR"
    ADMIN = "ADMIN"


class ModoContabilidad(str, Enum):
    ORDINARIO = "ORDINARIO"
    EXTRAORDINARIO_ORDINARIO = "EXTRAORDINARIO_ORDINARIO"
    EXTRAORDINARIO_NOCRITICO = "EXTRAORDINARIO_NOCRITICO"
    EXTRAORDINARIO_CRITICO = "EXTRAORDINARIO_CRITICO"


class CalificacionEntidad(str, Enum):
    IMAGEN_FIEL = "IMAGEN_FIEL"
    CALIDAD = "CALIDAD"
    MEDIO_AMBIENTE = "MEDIO_AMBIENTE"
    CLIMA = "CLIMA"


class CriticidadImporte(str, Enum):
    BAJA_INFORMATIVA = "BAJA_INFORMATIVA"
    MEDIA = "MEDIA"
    CUASI_CRITICA = "CUASI_CRITICA"
    CRITICA = "CRITICA"


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


_JERARQUIA_ROL: dict[str, int] = {
    Rol.AUXILIAR: 1,
    Rol.OPERARIO: 2,
    Rol.JEFE_CONTABILIDAD: 3,
    Rol.SUBDIRECTOR: 4,
    Rol.DIRECTOR: 5,
    Rol.ADMIN: 3,
}


@dataclass
class Actor:
    actor_id: str
    nombre: str
    tipo: str = "HUMANO"
    rol: Rol = Rol.OPERARIO

    @property
    def nivel_jerarquia(self) -> int:
        return _JERARQUIA_ROL[self.rol]

    def puede_ejecutar(self, otro_rol: "Rol") -> bool:
        return self.nivel_jerarquia >= _JERARQUIA_ROL[otro_rol]


@dataclass
class Autorizacion:
    autorizacion_id: str
    actor_id: str
    competencia: str
    alcance: str
    otorgada_en: datetime
    vigente_hasta: datetime | None = None
    revocada_en: datetime | None = None
    revocada_por: str | None = None
    motivo_revocacion: str | None = None


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
    autorizacion_id: str
    decidida_en: datetime
    estado: EstadoDecision = EstadoDecision.PROPUESTA

    def __post_init__(self) -> None:
        if not self.autorizacion_id or not self.autorizacion_id.strip():
            raise ValueError("La decisión requiere una autorización identificada")


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
    autorizacion_id: str
    estado: EstadoRepresentacion = EstadoRepresentacion.PROPUESTA
    registrada_en: datetime | None = None

    def __post_init__(self) -> None:
        if not self.autorizacion_id or not self.autorizacion_id.strip():
            raise ValueError("La representación requiere una autorización identificada")

    def cuadra(self) -> bool:
        return sum(l.debe for l in self.lineas) == sum(l.haber for l in self.lineas)


@dataclass(frozen=True)
class CierreContable:
    """Propuesta derivada de regularización, cierre y apertura.

    Las líneas son una hoja de trabajo. No son representaciones registradas
    ni modifican el mayor hasta que otro caso de uso las adopte expresamente.
    """

    cierre_id: str
    ejercicio_id: str
    fecha_cierre: datetime
    registrado_en: datetime
    regularizacion: tuple[Linea, ...]
    asiento_cierre: tuple[Linea, ...]
    asiento_apertura: tuple[Linea, ...]
    representacion_ids: tuple[str, ...]
    resultado_ejercicio: int


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


@dataclass
class PermisoConcedido:
    permiso_id: str
    otorgante_id: str
    beneficiario_id: str
    competencia: str
    alcance: str
    otorgada_en: datetime
    vigente_hasta: datetime | None = None
    revocada_en: datetime | None = None


@dataclass
class SolicitudAdmin:
    solicitud_id: str
    solicitante_id: str  # JEFE_CONTABILIDAD o DIRECTOR
    admin_id: str
    solicitada_en: datetime
    concluida_en: datetime | None = None
    informe_id: str | None = None


@dataclass
class InformeAdmin:
    informe_id: str
    solicitud_id: str
    redactado_por: str  # JEFE_CONTABILIDAD
    presentado_en: datetime
    repercusion_sustancia: str
    validado: bool | None = None
    graduacion_causa: str | None = None


@dataclass
class RemisionInvestigacion:
    remision_id: str
    hecho_economico_id: str
    promovido_por: str  # JEFE_CONTABILIDAD, SUBDIRECTOR o DIRECTOR
    promovida_en: datetime
    finalizada_en: datetime | None = None
    informe_id: str | None = None


@dataclass
class AlertaImporte:
    grupo: str
    subgrupo: str
    sub_subgrupo: str | None
    monto_umbral: int
    criticidad: CriticidadImporte
    notificar_a: str  # rol que recibe la notificación


@dataclass
class RegistroNoAsiento:
    registro_id: str
    tipo_registro: str
    ejecutado_por: str  # JEFE_CONTABILIDAD
    visado_por: str | None  # SUBDIRECTOR
    visado_en: datetime | None
    causa: str
    registrado_en: datetime
