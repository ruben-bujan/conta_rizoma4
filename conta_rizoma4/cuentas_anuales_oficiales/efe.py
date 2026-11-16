# -*- coding: utf-8 -*-
"""EFE (Estado de Flujos de Efectivo)."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EFE:
    """Estado de Flujos de Efectivo."""
    # Flujos de efectivo de las actividades de explotación
    resultado_antes_impuestos: int = 0
    ajustes_resultado: list[dict] = field(default_factory=list)
    cambios_capital_corriente: list[dict] = field(default_factory=list)
    otros_flujos_explotacion: list[dict] = field(default_factory=list)
    impuestos_pagados: int = 0

    # Flujos de efectivo de las actividades de inversión
    pagos_inmovilizado: int = 0
    cobros_inmovilizado: int = 0
    pagos_inversiones: int = 0
    cobros_inversiones: int = 0

    # Flujos de efectivo de las actividades de financiación
    cobros_aportaciones: int = 0
    pagos_dividendos: int = 0
    cobros_deudas: int = 0
    pagos_deudas: int = 0

    @property
    def flujo_explotacion(self) -> int:
        return (
            self.resultado_antes_impuestos +
            sum(a["importe"] for a in self.ajustes_resultado) +
            sum(c["importe"] for c in self.cambios_capital_corriente) +
            sum(o["importe"] for o in self.otros_flujos_explotacion) -
            self.impuestos_pagados
        )

    @property
    def flujo_inversion(self) -> int:
        return (
            -self.pagos_inmovilizado + self.cobros_inmovilizado -
            self.pagos_inversiones + self.cobros_inversiones
        )

    @property
    def flujo_financiacion(self) -> int:
        return (
            self.cobros_aportaciones - self.pagos_dividendos +
            self.cobros_deudas - self.pagos_deudas
        )

    @property
    def aumento_efectivo(self) -> int:
        return self.flujo_explotacion + self.flujo_inversion + self.flujo_financiacion


def formatear_efe(
    resultado_antes_impuestos: int,
    amortizacion: int,
    variacion_capital_corriente: int,
    impuestos_pagados: int,
    pagos_inmovilizado: int = 0,
    cobros_inmovilizado: int = 0,
    cobros_aportaciones: int = 0,
    pagos_dividendos: int = 0,
    cobros_deudas: int = 0,
    pagos_deudas: int = 0,
) -> EFE:
    """Construye el EFE con los datos básicos."""
    e = EFE()
    e.resultado_antes_impuestos = resultado_antes_impuestos
    e.ajustes_resultado = [{"concepto": "Amortización", "importe": amortizacion}]
    e.cambios_capital_corriente = [{"concepto": "Variación capital corriente", "importe": variacion_capital_corriente}]
    e.impuestos_pagados = impuestos_pagados
    e.pagos_inmovilizado = pagos_inmovilizado
    e.cobros_inmovilizado = cobros_inmovilizado
    e.cobros_aportaciones = cobros_aportaciones
    e.pagos_dividendos = pagos_dividendos
    e.cobros_deudas = cobros_deudas
    e.pagos_deudas = pagos_deudas
    return e
