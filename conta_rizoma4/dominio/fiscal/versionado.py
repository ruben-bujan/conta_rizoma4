"""Registro inmutable y temporal de reglas fiscales, sin catálogo legal incorporado."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


class ErrorReglaFiscal(ValueError):
    pass


@dataclass(frozen=True)
class ReglaFiscal:
    regla_id: str
    impuesto: str
    clave: str
    jurisdiccion: str
    version: str
    vigente_desde: date
    registrada_en: datetime
    parametros: tuple[tuple[str, str], ...]
    fuente_referencia: str
    vigente_hasta: date | None = None
    reemplaza_regla_id: str | None = None

    def __post_init__(self) -> None:
        if any(not valor for valor in (
            self.regla_id, self.impuesto, self.clave, self.jurisdiccion,
            self.version, self.fuente_referencia,
        )):
            raise ErrorReglaFiscal("Identificadores, versión y referencia de fuente son obligatorios")
        if self.vigente_hasta is not None and self.vigente_hasta <= self.vigente_desde:
            raise ErrorReglaFiscal("La vigencia final debe ser posterior a la inicial")
        if self.reemplaza_regla_id == self.regla_id:
            raise ErrorReglaFiscal("Una regla no puede reemplazarse a sí misma")
        if not isinstance(self.parametros, tuple) or any(
            not isinstance(par, tuple) or len(par) != 2
            or not isinstance(par[0], str) or not par[0].strip()
            or not isinstance(par[1], str)
            for par in self.parametros
        ):
            raise ErrorReglaFiscal("Los parámetros deben ser pares inmutables nombre/valor")
        nombres = [nombre for nombre, _ in self.parametros]
        if len(nombres) != len(set(nombres)):
            raise ErrorReglaFiscal("Los parámetros deben tener nombres únicos")

    def es_vigente(self, fecha: date) -> bool:
        return self.vigente_desde <= fecha and (
            self.vigente_hasta is None or fecha < self.vigente_hasta
        )


class RegistroFiscalMemoria:
    """Registro append-only con vigencia efectiva y fecha de conocimiento."""

    def __init__(self) -> None:
        self._reglas: list[ReglaFiscal] = []

    @property
    def reglas(self) -> tuple[ReglaFiscal, ...]:
        return tuple(self._reglas)

    def registrar(self, regla: ReglaFiscal) -> ReglaFiscal:
        if any(actual.regla_id == regla.regla_id for actual in self._reglas):
            raise ErrorReglaFiscal("Identificador de regla duplicado")
        if regla.reemplaza_regla_id:
            anterior = next(
                (r for r in self._reglas if r.regla_id == regla.reemplaza_regla_id), None
            )
            if anterior is None:
                raise ErrorReglaFiscal("La regla reemplazada no existe")
            if (anterior.impuesto, anterior.clave, anterior.jurisdiccion) != (
                regla.impuesto, regla.clave, regla.jurisdiccion
            ):
                raise ErrorReglaFiscal("La regla reemplazada debe corresponder al mismo ámbito")
            if regla.registrada_en < anterior.registrada_en:
                raise ErrorReglaFiscal("La corrección no puede conocerse antes que la regla sustituida")
            if any(r.reemplaza_regla_id == anterior.regla_id for r in self._reglas):
                raise ErrorReglaFiscal("La regla sustituida ya tiene una corrección; reemplace la versión vigente")
        if self._reglas and (
            (self._reglas[0].registrada_en.tzinfo is None)
            != (regla.registrada_en.tzinfo is None)
        ):
            raise ErrorReglaFiscal("No se pueden mezclar fechas de conocimiento con y sin zona horaria")
        self._reglas.append(regla)
        return regla

    def resolver(
        self, *, impuesto: str, clave: str, jurisdiccion: str,
        fecha_aplicacion: date, conocida_en: datetime,
    ) -> ReglaFiscal:
        if self._reglas and (
            (self._reglas[0].registrada_en.tzinfo is None)
            != (conocida_en.tzinfo is None)
        ):
            raise ErrorReglaFiscal("La fecha de consulta debe usar la misma convención horaria del registro")
        candidatas = [
            regla for regla in self._reglas
            if (regla.impuesto, regla.clave, regla.jurisdiccion)
            == (impuesto, clave, jurisdiccion)
            and regla.es_vigente(fecha_aplicacion)
            and regla.registrada_en <= conocida_en
        ]
        reemplazadas = {
            regla.reemplaza_regla_id for regla in candidatas if regla.reemplaza_regla_id
        }
        vigentes = [regla for regla in candidatas if regla.regla_id not in reemplazadas]
        if not vigentes:
            raise ErrorReglaFiscal("No hay regla conocida y vigente para la fecha solicitada")
        if len(vigentes) > 1:
            raise ErrorReglaFiscal("Hay reglas concurrentes; se requiere resolver el solapamiento")
        return vigentes[0]


@dataclass(frozen=True)
class AplicacionReglaFiscal:
    regla_id: str
    impuesto: str
    version: str
    fecha_aplicacion: date
    conocida_en: datetime
    parametros_aplicados: tuple[tuple[str, str], ...]


def documentar_aplicacion(
    registro: RegistroFiscalMemoria, *, impuesto: str, clave: str,
    jurisdiccion: str, fecha_aplicacion: date, conocida_en: datetime,
) -> AplicacionReglaFiscal:
    """Fija en un resultado qué versión se resolvió, sin calcular ni presentar impuestos."""
    regla = registro.resolver(
        impuesto=impuesto, clave=clave, jurisdiccion=jurisdiccion,
        fecha_aplicacion=fecha_aplicacion, conocida_en=conocida_en,
    )
    return AplicacionReglaFiscal(
        regla_id=regla.regla_id, impuesto=regla.impuesto, version=regla.version,
        fecha_aplicacion=fecha_aplicacion, conocida_en=conocida_en,
        parametros_aplicados=regla.parametros,
    )
