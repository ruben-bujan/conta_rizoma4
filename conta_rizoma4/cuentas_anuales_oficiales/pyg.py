# -*- coding: utf-8 -*-
"""Cuenta de PyG oficial (formato Registro Mercantil).

Modelos abreviado y normal, según RD 1514/2007.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PyGOficial:
    """Cuenta de pérdidas y ganancias formateada según el PGC."""
    # Importe neto de la cifra de negocios
    ingresos_por_ventas: int = 0
    prestacion_servicios: int = 0

    # Variación de existencias
    variacion_existencias: int = 0

    # Aprovisionamientos
    consumos_materias_primas: int = 0
    consumos_otros_aprov: int = 0

    # Otros ingresos de explotación
    otros_ingresos: int = 0

    # Gastos de personal
    sueldos_y_salarios: int = 0
    cargas_sociales: int = 0

    # Otros gastos de explotación
    arrendamientos: int = 0
    otros_servicios: int = 0

    # Amortización del inmovilizado
    amortizacion: int = 0

    # Deterioro y resultado por enajenaciones
    deterioro: int = 0
    resultado_enajenaciones: int = 0

    # Resultado financiero
    ingresos_financieros: int = 0
    gastos_financieros: int = 0

    # Impuesto sobre sociedades
    impuesto_sociedades: int = 0

    @property
    def resultado_explotacion(self) -> int:
        return (
            self.ingresos_por_ventas + self.prestacion_servicios +
            self.variacion_existencias + self.otros_ingresos -
            self.consumos_materias_primas - self.consumos_otros_aprov -
            self.sueldos_y_salarios - self.cargas_sociales -
            self.arrendamientos - self.otros_servicios -
            self.amortizacion - self.deterioro +
            self.resultado_enajenaciones
        )

    @property
    def resultado_financiero(self) -> int:
        return self.ingresos_financieros - self.gastos_financieros

    @property
    def resultado_antes_impuestos(self) -> int:
        return self.resultado_explotacion + self.resultado_financiero

    @property
    def resultado_ejercicio(self) -> int:
        return self.resultado_antes_impuestos - self.impuesto_sociedades


def formatear_pyg(pyg: dict, gastos: dict, ingresos: dict) -> PyGOficial:
    """Convierte la cuenta de PyG al formato oficial.

    Args:
        pyg: dict con "resultado", "total_gastos", "total_ingresos"
        gastos: {cuenta: importe} (grupo 6)
        ingresos: {cuenta: importe} (grupo 7)
    """
    p = PyGOficial()
    for cuenta, importe in ingresos.items():
        if cuenta.startswith("700"):
            p.ingresos_por_ventas += importe
        elif cuenta.startswith("705"):
            p.prestacion_servicios += importe
        elif cuenta.startswith("74"):
            p.otros_ingresos += importe
        elif cuenta.startswith("76"):
            p.ingresos_financieros += importe
    for cuenta, importe in gastos.items():
        if cuenta.startswith("600") or cuenta.startswith("601"):
            p.consumos_materias_primas += importe
        elif cuenta.startswith("602"):
            p.consumos_otros_aprov += importe
        elif cuenta.startswith("640"):
            p.sueldos_y_salarios += importe
        elif cuenta.startswith("642"):
            p.cargas_sociales += importe
        elif cuenta.startswith("621"):
            p.arrendamientos += importe
        elif cuenta.startswith("62"):
            p.otros_servicios += importe
        elif cuenta.startswith("68"):
            p.amortizacion += importe
        elif cuenta.startswith("66"):
            p.gastos_financieros += importe
        elif cuenta.startswith("630"):
            p.impuesto_sociedades += importe
    return p
