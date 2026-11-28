"""Entidades económicas mínimas promovidas desde la POC."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class TipoFecha(str, Enum):
    EXACTA = "EXACTA"
    ESTIMADA = "ESTIMADA"
    RANGO = "RANGO"
    DESCONOCIDA = "DESCONOCIDA"


class EstadoEpistemologico(str, Enum):
    NO_ACREDITADO = "NO_ACREDITADO"
    DECLARADO = "DECLARADO"
    CONTRASTADO_PARCIALMENTE = "CONTRASTADO_PARCIALMENTE"
    ACREDITADO = "ACREDITADO"
    CONTRADICHO = "CONTRADICHO"
    RECTIFICADO = "RECTIFICADO"
    RECHAZADO = "RECHAZADO"


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
class Tercero:
    tercero_id: str
    tipo: str
    nombre: str
    identificador_fiscal: str | None = None
    identidad_fiscal_estado: str = "NO_VERIFICADA"
    pais: str | None = None
    activo: bool = True
    metadatos: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.tercero_id:
            raise ValueError("tercero_id es obligatorio")
        if not self.tipo:
            raise ValueError("tipo de tercero es obligatorio")


@dataclass
class EjercicioContable:
    ejercicio_id: str
    entidad_id: str
    inicio: datetime
    fin: datetime
    estado: str = "ABIERTO"

    def __post_init__(self) -> None:
        if not self.ejercicio_id:
            raise ValueError("ejercicio_id es obligatorio")
        if self.fin < self.inicio:
            raise ValueError("La fecha fin no puede preceder a la fecha inicio")

    @property
    def permite_registro(self) -> bool:
        """Abierto a nuevos registros, también tras reapertura autorizada."""
        return self.estado in {"ABIERTO", "REABIERTO"}


@dataclass
class MovimientoEconomico:
    movimiento_id: str
    entidad_id: str
    tercero_id: str
    tipo: str
    importe: int
    moneda: str = "EUR"
    fecha_documental: datetime | None = None
    fecha_vencimiento: datetime | None = None
    estado: str = "PENDIENTE"

    def __post_init__(self) -> None:
        if self.importe < 0:
            raise ValueError("El importe no puede ser negativo")
        if not self.tipo:
            raise ValueError("tipo de movimiento obligatorio")


@dataclass
class CuentaBancaria:
    cuenta_id: str
    entidad_id: str
    iban: str
    moneda: str = "EUR"
    nombre: str = ""
    activa: bool = True


@dataclass
class MovimientoExtracto:
    movimiento_id: str
    cuenta_id: str
    fecha_operacion: datetime
    fecha_valor: datetime | None
    importe: int
    descripcion: str
    referencia: str | None = None
    estado: str = "NO_CONCILIADO"


@dataclass
class Conciliacion:
    conciliacion_id: str
    movimiento_extracto_id: str
    movimiento_economico_id: str | None
    estado: str
    diferencia: int = 0
    motivo: str = ""


@dataclass
class Vencimiento:
    vencimiento_id: str
    movimiento_id: str
    entidad_id: str
    tercero_id: str
    tipo: str
    importe: int
    moneda: str = "EUR"
    fecha_vencimiento: datetime | None = None
    estado: str = "PENDIENTE"

    def __post_init__(self) -> None:
        if self.importe < 0:
            raise ValueError("El importe no puede ser negativo")
        if not self.tipo:
            raise ValueError("Tipo de vencimiento obligatorio")
