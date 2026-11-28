"""Adaptadores opcionales entre la POC y el código contable existente.

La POC no depende de estos adaptadores. Este módulo permite reutilizar los
modelos probados de partida doble y los actos puros sin incorporar PostgreSQL
ni FastAPI al núcleo epistemológico.
"""
from __future__ import annotations

from datetime import date
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, Callable, Iterable
import sys

from .modelo import Linea as LineaPOC


_RAIZ = Path(__file__).resolve().parents[1]


def _cargar_modelo_actual():
    ruta = _RAIZ / "conta_rizoma4" / "partida_doble" / "modelo.py"
    nombre = "conta_rizoma4_poc_modelo_actual"
    spec = spec_from_file_location(nombre, ruta)
    if spec is None or spec.loader is None:
        raise RuntimeError("No se pudo cargar el modelo contable actual")
    modulo = module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def linea_poc_a_actual(linea: LineaPOC):
    """Convierte una línea mínima POC a la línea contable existente."""
    modelo = _cargar_modelo_actual()
    return modelo.Linea(
        cuenta_pgc=linea.cuenta,
        debe_centimos=linea.debe,
        haber_centimos=linea.haber,
    )


def linea_actual_a_poc(linea) -> LineaPOC:
    """Convierte una línea contable existente a la representación mínima POC."""
    return LineaPOC(
        cuenta=linea.cuenta_pgc,
        debe=linea.debe_centimos,
        haber=linea.haber_centimos,
    )


def representacion_poc_a_asiento(
    *,
    indice: int,
    fecha: date,
    concepto: str,
    lineas_poc: Iterable[LineaPOC],
    hash_previo: str,
    metadatos: dict[str, Any] | None = None,
):
    """Construye un Asiento actual sin persistencia ni backend externo."""
    modelo = _cargar_modelo_actual()
    lineas_actuales = tuple(linea_poc_a_actual(l) for l in lineas_poc)
    total_debe = sum(l.debe_centimos for l in lineas_actuales)
    total_haber = sum(l.haber_centimos for l in lineas_actuales)
    if total_debe != total_haber:
        raise modelo.PartidaDobleError(
            f"descuadre: debe={total_debe} haber={total_haber}"
        )

    ruta_asiento = _RAIZ / "conta_rizoma4" / "operativo" / "asiento.py"
    nombre_asiento = "conta_rizoma4_poc_asiento_actual"
    spec_asiento = spec_from_file_location(nombre_asiento, ruta_asiento)
    if spec_asiento is None or spec_asiento.loader is None:
        raise RuntimeError("No se pudo cargar el hash contable heredado")
    modulo_asiento = module_from_spec(spec_asiento)
    sys.modules[nombre_asiento] = modulo_asiento
    spec_asiento.loader.exec_module(modulo_asiento)

    contenido = {
        "fecha": fecha.isoformat(),
        "concepto": concepto,
        "lineas": [
            {
                "cuenta_pgc": l.cuenta_pgc,
                "debe_centimos": l.debe_centimos,
                "haber_centimos": l.haber_centimos,
                "parrafo_pgc_id": l.parrafo_pgc_id,
                "concepto_linea": l.concepto_linea,
            }
            for l in lineas_actuales
        ],
        "metadatos": metadatos or {},
    }
    huella = modulo_asiento.calcular_huella(contenido)
    hash_actual = modulo_asiento.calcular_hash(huella, hash_previo, indice)
    return modelo.Asiento(
        indice=indice,
        fecha=fecha,
        concepto=concepto,
        lineas=lineas_actuales,
        hash_previo=hash_previo,
        hash=hash_actual,
        huella_contenido=huella,
        metadatos=metadatos or {},
    )


def asiento_actual_a_lineas_poc(asiento) -> tuple[LineaPOC, ...]:
    """Extrae las líneas existentes como representación mínima POC."""
    return tuple(linea_actual_a_poc(l) for l in asiento.lineas)


def adaptar_acto_puro(
    acto: Callable[..., Any],
    **parametros: Any,
):
    """Ejecuta una función pura si sus dependencias ya están disponibles.

    No importa ni activa PostgreSQL. Se conserva como puerto de compatibilidad
    para migrar actos puros una vez su importación ya no esté acoplada al
    paquete operativo heredado.
    """
    return acto(**parametros)
