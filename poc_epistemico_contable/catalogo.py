"""Adaptador de catálogo de actos sin importar ni ejecutar el paquete legado.

Clasifica los códigos por responsabilidad epistemológica: representación,
hecho económico, obligación declarativa, cierre o operación de consolidación.
Este catálogo no persiste ni genera asientos por sí mismo.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


_RAIZ = Path(__file__).resolve().parents[1]
_ACTOS_DIR = _RAIZ / "conta_rizoma4" / "actos"


@dataclass(frozen=True)
class ActoCatalogado:
    codigo: str
    archivo: str
    grupo: str
    responsabilidad: str
    genera_asiento: bool


_DECLARATIVOS = {
    "A_MODELO_347",
    "A_MODELO_349",
    "A_MODELO_369",
    "A_MODELO_390",
    "A_RESUMEN_ANUAL_390",
    "A_MODELO_720",
    "A_MODELO_721",
    "A_MODELO_714",
}

_CIERRE = {
    "A_REGULARIZACION_GRUPOS_6_7",
    "A_CIERRE_EJERCICIO",
    "A_APERTURA_EJERCICIO",
}

_CONSOLIDACION = {
    "A_ELIMINACION_INTRAGRUPO",
    "A_ATRIBUCION_SOCIOS_MINORITARIOS",
}


def _grupo_desde_nombre(nombre: str) -> str:
    if nombre.endswith(".py"):
        nombre = nombre[:-3]
    return nombre


def _responsabilidad(codigo: str) -> tuple[str, bool]:
    if codigo in _DECLARATIVOS:
        return "OBLIGACION_DECLARATIVA", False
    if codigo in _CIERRE:
        return "OPERACION_DE_CIERRE", True
    if codigo in _CONSOLIDACION:
        return "CONSOLIDACION", True

    nombre = codigo.lower()
    if "informativo" in nombre:
        return "OBLIGACION_DECLARATIVA", False
    if any(token in nombre for token in (
        "rectific", "reversion", "reclasific", "regularizacion",
        "cambio_criterio", "error_ejercicio",
    )):
        return "RECTIFICACION_O_RECLASIFICACION", True
    if any(token in nombre for token in (
        "factura", "cobro", "pago", "nomina", "compra", "venta",
        "impuesto", "iva", "irpf", "is", "dividendo", "capital",
        "leasing", "amortizacion", "deterioro", "existencias",
        "subvencion", "periodificacion", "provision", "cobertura",
    )):
        return "HECHO_O_REPRESENTACION_ECONOMICA", True
    return "REPRESENTACION_CONTABLE", True


def cargar_catalogo() -> tuple[ActoCatalogado, ...]:
    """Lee los códigos definidos por cada diccionario ACTOS, sin importar Python."""
    catalogo: list[ActoCatalogado] = []

    for ruta in sorted(_ACTOS_DIR.glob("*.py")):
        if ruta.name == "__init__.py":
            continue
        arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
        grupo = _grupo_desde_nombre(ruta.name)

        for nodo in arbol.body:
            if not isinstance(nodo, ast.Assign):
                continue
            es_actos = any(
                isinstance(objetivo, ast.Name) and objetivo.id == "ACTOS"
                for objetivo in nodo.targets
            )
            if not es_actos or not isinstance(nodo.value, ast.Dict):
                continue

            for clave in nodo.value.keys:
                if not isinstance(clave, ast.Constant) or not isinstance(clave.value, str):
                    continue
                codigo = clave.value
                responsabilidad, genera_asiento = _responsabilidad(codigo)
                catalogo.append(ActoCatalogado(
                    codigo=codigo,
                    archivo=ruta.name,
                    grupo=grupo,
                    responsabilidad=responsabilidad,
                    genera_asiento=genera_asiento,
                ))

    sin_duplicados = {item.codigo: item for item in catalogo}
    if len(sin_duplicados) != len(catalogo):
        raise RuntimeError("El catálogo contiene códigos duplicados")
    return tuple(sorted(sin_duplicados.values(), key=lambda item: item.codigo))


def resumen_catalogo() -> dict[str, int]:
    catalogo = cargar_catalogo()
    resumen: dict[str, int] = {}
    for item in catalogo:
        resumen[item.responsabilidad] = resumen.get(item.responsabilidad, 0) + 1
    return resumen
