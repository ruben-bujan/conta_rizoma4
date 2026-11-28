"""Modelos fiscales básicos en memoria. No generan asientos ni declaraciones."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from .versionado import (
    AplicacionReglaFiscal, ErrorReglaFiscal, RegistroFiscalMemoria,
    documentar_aplicacion,
)


@dataclass
class Modelo303:
    iva_repercutido: int = 0
    iva_soportado: int = 0
    compensacion_anterior: int = 0

    @property
    def diferencia(self) -> int:
        return self.iva_repercutido - self.iva_soportado

    @property
    def resultado(self) -> str:
        if self.diferencia > 0:
            return "A_INGRESAR"
        if self.diferencia < 0:
            return "A_DEVOLVER_O_COMPENSAR"
        return "SIN_DIFERENCIA"


@dataclass
class Modelo200:
    resultado_contable: int = 0
    ajustes_positivos: int = 0
    ajustes_negativos: int = 0
    compensacion_bases: int = 0
    tipo_impositivo: Decimal | float | int | None = None

    def __post_init__(self) -> None:
        for nombre in ("resultado_contable", "ajustes_positivos", "ajustes_negativos", "compensacion_bases"):
            valor = getattr(self, nombre)
            if type(valor) is not int:
                raise ValueError(f"{nombre} debe expresarse como céntimos enteros")
        for nombre in ("ajustes_positivos", "ajustes_negativos", "compensacion_bases"):
            if getattr(self, nombre) < 0:
                raise ValueError(f"{nombre} no puede ser negativo")
        try:
            if self.tipo_impositivo is None:
                raise InvalidOperation
            tipo = Decimal(str(self.tipo_impositivo))
        except (InvalidOperation, ValueError):
            raise ValueError("tipo_impositivo no es válido") from None
        if not tipo.is_finite() or not Decimal(0) <= tipo <= Decimal(100):
            raise ValueError("tipo_impositivo debe estar entre 0 y 100")

    @property
    def base_imponible(self) -> int:
        previa = self.resultado_contable + self.ajustes_positivos - self.ajustes_negativos
        return max(0, previa - self.compensacion_bases)

    @property
    def cuota_integra(self) -> int:
        if self.tipo_impositivo is None:  # Salvaguarda para objetos alterados tras crearse.
            raise ValueError("tipo_impositivo es obligatorio")
        tipo = Decimal(str(self.tipo_impositivo))
        return int((Decimal(self.base_imponible) * tipo / Decimal(100)).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP,
        ))


@dataclass(frozen=True)
class ResultadoModelo200Versionado:
    calculo: Modelo200
    aplicacion_regla: AplicacionReglaFiscal


@dataclass(frozen=True)
class ResultadoImporteFiscal:
    importe_centimos: int
    aplicacion_regla: AplicacionReglaFiscal


@dataclass(frozen=True)
class ResultadoModelo303Versionado:
    calculo: Modelo303
    aplicaciones_regla: tuple[AplicacionReglaFiscal, AplicacionReglaFiscal]


def calcular_importe_con_regla(
    registro: RegistroFiscalMemoria,
    *, impuesto: str, clave: str, jurisdiccion: str,
    fecha_aplicacion: date, conocida_en: datetime, base_centimos: int,
) -> ResultadoImporteFiscal:
    """Aplica un porcentaje versionado a una base monetaria en céntimos."""
    if type(base_centimos) is not int or base_centimos < 0:
        raise ErrorReglaFiscal("La base fiscal debe ser un entero de céntimos no negativo")
    aplicacion = documentar_aplicacion(
        registro, impuesto=impuesto, clave=clave, jurisdiccion=jurisdiccion,
        fecha_aplicacion=fecha_aplicacion, conocida_en=conocida_en,
    )
    parametros = dict(aplicacion.parametros_aplicados)
    try:
        tipo = Decimal(parametros["tipo_pct"])
    except (KeyError, InvalidOperation, ValueError):
        raise ErrorReglaFiscal("La regla fiscal requiere un parámetro tipo_pct válido") from None
    if not tipo.is_finite() or not Decimal(0) <= tipo <= Decimal(100):
        raise ErrorReglaFiscal("tipo_pct debe estar entre 0 y 100")
    importe = int((Decimal(base_centimos) * tipo / Decimal(100)).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP,
    ))
    return ResultadoImporteFiscal(importe, aplicacion)


def calcular_modelo_200_versionado(
    registro: RegistroFiscalMemoria,
    *, clave: str, jurisdiccion: str, fecha_aplicacion: date,
    conocida_en: datetime, resultado_contable: int,
    ajustes_positivos: int = 0, ajustes_negativos: int = 0,
    compensacion_bases: int = 0,
) -> ResultadoModelo200Versionado:
    """Calcula cuota simplificada con el tipo de IS resuelto y deja su versión trazada.

    El registro debe contener el parámetro textual ``tipo_pct``. No selecciona
    tipos legales por sí mismo ni supone que el cálculo cubra un modelo 200 oficial.
    """
    aplicacion = documentar_aplicacion(
        registro, impuesto="IS", clave=clave, jurisdiccion=jurisdiccion,
        fecha_aplicacion=fecha_aplicacion, conocida_en=conocida_en,
    )
    parametros = dict(aplicacion.parametros_aplicados)
    try:
        tipo = Decimal(parametros["tipo_pct"])
    except (KeyError, InvalidOperation, ValueError):
        raise ErrorReglaFiscal("La regla de IS requiere un parámetro tipo_pct válido") from None
    if not tipo.is_finite() or not Decimal(0) <= tipo <= Decimal(100):
        raise ErrorReglaFiscal("tipo_pct debe estar entre 0 y 100")
    calculo = Modelo200(
        resultado_contable=resultado_contable,
        ajustes_positivos=ajustes_positivos,
        ajustes_negativos=ajustes_negativos,
        compensacion_bases=compensacion_bases,
        tipo_impositivo=tipo,
    )
    return ResultadoModelo200Versionado(calculo, aplicacion)


def calcular_modelo_303_versionado(
    registro: RegistroFiscalMemoria,
    *, jurisdiccion: str, fecha_aplicacion: date, conocida_en: datetime,
    clave_repercutido: str, clave_soportado: str,
    base_repercutida_centimos: int, base_soportada_centimos: int,
) -> ResultadoModelo303Versionado:
    """Calcula un 303 analítico con tipos versionados para dos bases simples.

    No determina deducibilidad, regímenes especiales, ajustes, prorrata ni
    compensaciones; no es un cálculo completo del formulario oficial.
    """
    repercutido = calcular_importe_con_regla(
        registro, impuesto="IVA", clave=clave_repercutido,
        jurisdiccion=jurisdiccion, fecha_aplicacion=fecha_aplicacion,
        conocida_en=conocida_en, base_centimos=base_repercutida_centimos,
    )
    soportado = calcular_importe_con_regla(
        registro, impuesto="IVA", clave=clave_soportado,
        jurisdiccion=jurisdiccion, fecha_aplicacion=fecha_aplicacion,
        conocida_en=conocida_en, base_centimos=base_soportada_centimos,
    )
    modelo = Modelo303(
        iva_repercutido=repercutido.importe_centimos,
        iva_soportado=soportado.importe_centimos,
    )
    return ResultadoModelo303Versionado(
        modelo, (repercutido.aplicacion_regla, soportado.aplicacion_regla),
    )
