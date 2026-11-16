# -*- coding: utf-8 -*-
"""Balance de situación oficial (formato Registro Mercantil).

Modelos abreviado y normal, según RD 1514/2007.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BalanceOficial:
    """Balance de situación formateado según el PGC."""
    # Activo no corriente
    inmovilizado_intangible: int = 0
    inmovilizado_material: int = 0
    inversiones_inmobiliarias: int = 0
    inversiones_financieras_lp: int = 0
    activos_por_impuesto_diferido: int = 0

    # Activo corriente
    existencias: int = 0
    deudores_comerciales: int = 0
    inversiones_financieras_cp: int = 0
    efectivo: int = 0

    # Patrimonio neto
    capital: int = 0
    prima_emision: int = 0
    reservas: int = 0
    resultado_ejercicio: int = 0

    # Pasivo no corriente
    deudas_lp: int = 0

    # Pasivo corriente
    deudas_cp: int = 0
    acreedores_comerciales: int = 0

    @property
    def total_activo_no_corriente(self) -> int:
        return (
            self.inmovilizado_intangible + self.inmovilizado_material +
            self.inversiones_inmobiliarias + self.inversiones_financieras_lp +
            self.activos_por_impuesto_diferido
        )

    @property
    def total_activo_corriente(self) -> int:
        return (
            self.existencias + self.deudores_comerciales +
            self.inversiones_financieras_cp + self.efectivo
        )

    @property
    def total_activo(self) -> int:
        return self.total_activo_no_corriente + self.total_activo_corriente

    @property
    def total_patrimonio_neto(self) -> int:
        return (
            self.capital + self.prima_emision + self.reservas +
            self.resultado_ejercicio
        )

    @property
    def total_pasivo_no_corriente(self) -> int:
        return self.deudas_lp

    @property
    def total_pasivo_corriente(self) -> int:
        return self.deudas_cp + self.acreedores_comerciales

    @property
    def total_pasivo(self) -> int:
        return self.total_pasivo_no_corriente + self.total_pasivo_corriente

    @property
    def total_patrimonio_neto_y_pasivo(self) -> int:
        return self.total_patrimonio_neto + self.total_pasivo

    @property
    def cuadra(self) -> bool:
        return self.total_activo == self.total_patrimonio_neto_y_pasivo


def formatear_balance(activo: dict, pasivo: dict, resultado: int) -> BalanceOficial:
    """Convierte el balance de cuentas_anuales al formato oficial.

    Args:
        activo: {grupo: {cuenta: importe}} (de balance_situacion)
        pasivo: {grupo: {cuenta: importe}}
        resultado: int
    """
    b = BalanceOficial()
    b.resultado_ejercicio = resultado

    # Activo no corriente (grupo 2)
    for cuenta, importe in activo.get(2, {}).items():
        if cuenta.startswith("20"):
            b.inmovilizado_intangible += importe
        elif cuenta.startswith("21"):
            b.inmovilizado_material += importe
        elif cuenta.startswith("22"):
            b.inversiones_inmobiliarias += importe
        elif cuenta.startswith("24"):
            b.inversiones_financieras_lp += importe
        elif cuenta.startswith("474"):
            b.activos_por_impuesto_diferido += importe

    # Activo corriente (grupo 3 = existencias)
    for cuenta, importe in activo.get(3, {}).items():
        b.existencias += importe

    # Activo corriente (grupo 4 = deudores)
    for cuenta, importe in activo.get(4, {}).items():
        if cuenta.startswith("43"):
            b.deudores_comerciales += importe
        elif cuenta.startswith("44"):
            b.inversiones_financieras_cp += importe

    # Efectivo (grupo 5)
    for cuenta, importe in activo.get(5, {}).items():
        if cuenta.startswith("57"):
            b.efectivo += importe

    # Patrimonio neto (grupo 1)
    for cuenta, importe in pasivo.get(1, {}).items():
        if cuenta.startswith("10"):
            b.capital += importe
        elif cuenta.startswith("11"):
            b.reservas += importe
        elif cuenta.startswith("12"):
            b.resultado_ejercicio += importe
        elif cuenta.startswith("13"):
            b.reservas += importe

    # Pasivo no corriente (grupo 1, deudas a largo plazo)
    for cuenta, importe in pasivo.get(1, {}).items():
        if cuenta.startswith("17"):
            b.deudas_lp += importe

    # Pasivo corriente (grupo 4 = acreedores)
    for cuenta, importe in pasivo.get(4, {}).items():
        if cuenta.startswith("40"):
            b.acreedores_comerciales += importe
        elif cuenta.startswith("52"):
            b.deudas_cp += importe

    return b
