# -*- coding: utf-8 -*-
"""Memoria resumida (formato Registro Mercantil)."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Memoria:
    """Memoria resumida con las notas principales."""
    actividad: str = ""
    bases_presentacion: str = ""
    aplicacion_resultados: str = ""
    version_normativa: str = ""
    normas_registro_valoracion: dict = field(default_factory=dict)
    inmovilizado_material: dict = field(default_factory=dict)
    inmovilizado_intangible: dict = field(default_factory=dict)
    arrendamientos: dict = field(default_factory=dict)
    instrumentos_financieros: dict = field(default_factory=dict)
    existencias: dict = field(default_factory=dict)
    patrimonio_neto: dict = field(default_factory=dict)
    impuesto_sociedades: dict = field(default_factory=dict)
    ingresos_gastos: dict = field(default_factory=dict)
    subvenciones: dict = field(default_factory=dict)
    hechos_posteriores: str = ""
    propuesta_aplicacion_resultados: dict = field(default_factory=dict)


def formatear_memoria(
    actividad: str,
    resultado_ejercicio: int,
    capital: int,
    reservas: int,
    *,
    bases_presentacion: str = "",
    aplicacion_resultados: str = "",
    propuesta_aplicacion_resultados: dict | None = None,
    version_normativa: str = "",
) -> Memoria:
    """Agrupa datos aportados; no presupone norma aplicada ni destino del resultado."""
    m = Memoria()
    m.actividad = actividad
    m.bases_presentacion = bases_presentacion
    m.aplicacion_resultados = aplicacion_resultados
    m.version_normativa = version_normativa
    m.patrimonio_neto = {
        "capital": capital,
        "reservas": reservas,
        "resultado_ejercicio": resultado_ejercicio,
    }
    m.propuesta_aplicacion_resultados = dict(propuesta_aplicacion_resultados or {})
    return m
