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
) -> Memoria:
    """Construye la memoria resumida."""
    m = Memoria()
    m.actividad = actividad
    m.bases_presentacion = (
        "Las cuentas anuales se han formulado según el PGC (RD 1514/2007)."
    )
    m.aplicacion_resultados = f"Resultado del ejercicio: {resultado_ejercicio} céntimos"
    m.patrimonio_neto = {
        "capital": capital,
        "reservas": reservas,
        "resultado_ejercicio": resultado_ejercicio,
    }
    m.propuesta_aplicacion_resultados = {
        "a_reservas": resultado_ejercicio if resultado_ejercicio > 0 else 0,
        "a_compensacion_perdidas": abs(resultado_ejercicio) if resultado_ejercicio < 0 else 0,
    }
    return m
