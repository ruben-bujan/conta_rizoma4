"""Constructor aislado de asientos INCIV en memoria.

No conecta con PostgreSQL, no escribe archivos ni genera documentos CAS.
La entrada procede de una copia extraída del libro diario 0302T.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable


RAIZ = Path(__file__).resolve().parent.parent
CSV_IN = RAIZ / "mdb_extraido_InCiv2010" / "0302T.csv"
EMPRESA_FUNCIONAL = "INCIVSA"
EMPRESA_HEREDADA = "INCIV_2010"


@dataclass(frozen=True)
class LineaEnsayo:
    cuenta: str
    debe_centimos: int
    haber_centimos: int
    persona: str | None = None

    def __post_init__(self) -> None:
        if not self.cuenta:
            raise ValueError("cuenta vacía")
        if self.debe_centimos < 0 or self.haber_centimos < 0:
            raise ValueError("importe negativo sin clasificación")
        if self.debe_centimos and self.haber_centimos:
            raise ValueError("la línea tiene debe y haber simultáneos")


@dataclass(frozen=True)
class AsientoEnsayo:
    codigo_origen: str
    fecha: datetime
    concepto: str
    lineas: tuple[LineaEnsayo, ...]

    @property
    def cuadra(self) -> bool:
        return (
            sum(linea.debe_centimos for linea in self.lineas)
            == sum(linea.haber_centimos for linea in self.lineas)
        )


@dataclass(frozen=True)
class GrupoOrigen:
    codigo_origen: str
    fecha_origen: str
    filas_originales: tuple[tuple[str, ...], ...]
    estado_migracion: str
    lineas: tuple[LineaEnsayo, ...] = ()
    error: str | None = None

    @property
    def clave_origen(self) -> str:
        return f"{self.codigo_origen}\x1f{self.fecha_origen}"


@dataclass
class ResultadoConstructor:
    asientos: list[AsientoEnsayo] = field(default_factory=list)
    grupos_totales: int = 0
    grupos_cuadrados: int = 0
    grupos_descuadrados: int = 0
    grupos_subdivididos: int = 0
    filas_omitir: int = 0
    errores_origen: list[dict] = field(default_factory=list)
    grupos_origen: list[GrupoOrigen] = field(default_factory=list)


def _parse_fecha(valor: str) -> datetime:
    valor = valor.strip()
    for formato in (
        "%m/%d/%y %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(valor, formato)
        except ValueError:
            continue
    raise ValueError(f"fecha no reconocida: {valor!r}")


def _parse_importe(valor: str) -> int:
    valor = valor.strip()
    if not valor:
        return 0
    try:
        numero = Decimal(valor.replace(",", ""))
    except InvalidOperation as exc:
        raise ValueError("importe no numérico") from exc
    if not numero.is_finite():
        raise ValueError("importe no finito")
    centimos = numero * 100
    if centimos != centimos.to_integral_value():
        raise ValueError("importe con más de dos decimales")
    return int(centimos)


def _cuenta(codigo: str) -> str:
    return codigo.split("/")[0].replace(" ", "").strip()[:30]


def _construir_lineas(filas: Iterable[list[str]]) -> tuple[LineaEnsayo, ...]:
    lineas: list[LineaEnsayo] = []
    for fila in filas:
        if len(fila) < 13:
            continue

        cuenta = _cuenta(fila[8])
        debe = _parse_importe(fila[11])
        haber = _parse_importe(fila[12])

        if debe < 0 and haber == 0:
            haber, debe = -debe, 0
        elif haber < 0 and debe == 0:
            debe, haber = -haber, 0

        if debe == 0 and haber == 0:
            continue

        persona = fila[10].strip() if len(fila) > 10 else ""
        lineas.append(LineaEnsayo(
            cuenta=cuenta,
            debe_centimos=debe,
            haber_centimos=haber,
            persona=persona or None,
        ))

    return tuple(lineas)


def construir_desde_csv(ruta: Path = CSV_IN) -> ResultadoConstructor:
    if not ruta.exists():
        raise FileNotFoundError(ruta)

    grupos: dict[tuple[str, str], list[list[str]]] = defaultdict(list)
    filas_omitir = 0

    with ruta.open(encoding="latin-1", newline="") as fichero:
        lector = csv.reader(fichero)
        next(lector, None)

        for fila in lector:
            if len(fila) < 13:
                filas_omitir += 1
                continue

            codigo_asiento = fila[5].strip()
            fecha = fila[6].strip()
            if not codigo_asiento or not fecha:
                filas_omitir += 1
                continue

            grupos[(codigo_asiento, fecha)].append(fila)

    resultado = ResultadoConstructor(
        grupos_totales=len(grupos),
        filas_omitir=filas_omitir,
    )

    for (codigo, fecha_texto), filas in sorted(grupos.items(), key=lambda item: item[0]):
        try:
            fecha = _parse_fecha(fecha_texto)
        except ValueError as exc:
            resultado.grupos_descuadrados += 1
            resultado.grupos_origen.append(GrupoOrigen(
                codigo, fecha_texto, tuple(tuple(f) for f in filas),
                "NO_DETERMINADO_FECHA", error="FECHA_INVALIDA",
            ))
            resultado.errores_origen.append({
                "codigo_asiento": codigo,
                "fecha": fecha_texto,
                "tipo": "FECHA_INVALIDA",
                "detalle": str(exc),
            })
            continue

        concepto = max(
            (fila[7].strip() for fila in filas if len(fila) > 7 and fila[7].strip()),
            key=len,
            default="",
        )
        try:
            lineas = _construir_lineas(filas)
        except ValueError as exc:
            resultado.grupos_descuadrados += 1
            resultado.grupos_origen.append(GrupoOrigen(
                codigo, fecha_texto, tuple(tuple(f) for f in filas),
                "NO_DETERMINADO_PRECISION_O_LINEA", error="LINEA_ORIGEN_INVALIDA",
            ))
            resultado.errores_origen.append({
                "codigo_asiento": codigo,
                "fecha": fecha_texto,
                "tipo": "LINEA_ORIGEN_INVALIDA",
                "detalle": str(exc),
            })
            continue

        if lineas:
            asiento = AsientoEnsayo(
                codigo_origen=codigo,
                fecha=fecha,
                concepto=concepto,
                lineas=lineas,
            )
            if asiento.cuadra:
                resultado.asientos.append(asiento)
                resultado.grupos_cuadrados += 1
                resultado.grupos_origen.append(GrupoOrigen(
                    codigo, fecha_texto, tuple(tuple(f) for f in filas),
                    "CANDIDATO_CUADRADO", lineas=lineas,
                ))
                continue

        resultado.grupos_descuadrados += 1
        resultado.grupos_origen.append(GrupoOrigen(
            codigo, fecha_texto, tuple(tuple(f) for f in filas),
            "NO_DETERMINADO_DESCUADRE", lineas=lineas,
        ))

        conceptos: dict[str, list[list[str]]] = defaultdict(list)
        for fila in filas:
            concepto_fila = fila[7].strip() if len(fila) > 7 else ""
            conceptos[concepto_fila].append(fila)

        for concepto_fila, filas_concepto in conceptos.items():
            lineas_concepto = _construir_lineas(filas_concepto)
            if not lineas_concepto:
                continue

            asiento_concepto = AsientoEnsayo(
                codigo_origen=codigo,
                fecha=fecha,
                concepto=concepto_fila or concepto,
                lineas=lineas_concepto,
            )
            if asiento_concepto.cuadra:
                resultado.asientos.append(asiento_concepto)
                resultado.grupos_subdivididos += 1
                resultado.grupos_cuadrados += 1

    return resultado
