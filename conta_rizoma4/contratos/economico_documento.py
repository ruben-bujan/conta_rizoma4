# -*- coding: utf-8 -*-
"""C — Tipo de documento económico (23 tipos)."""
from __future__ import annotations

from enum import Enum


class TipoDocumento(str, Enum):
    # Facturación
    FACTURA_EMITIDA = "FACTURA_EMITIDA"
    FACTURA_RECIBIDA = "FACTURA_RECIBIDA"
    FACTURA_RECTIFICATIVA_EMITIDA = "FACTURA_RECTIFICATIVA_EMITIDA"
    FACTURA_RECTIFICATIVA_RECIBIDA = "FACTURA_RECTIFICATIVA_RECIBIDA"
    NOTA_DE_ABONO = "NOTA_DE_ABONO"
    # Nóminas y Seguridad Social
    NOMINA = "NOMINA"
    TC1 = "TC1"  # boletín de cotización
    TC2 = "TC2"  # relación nominal de trabajadores
    # Bancarios
    EXTRACTO_BANCARIO = "EXTRACTO_BANCARIO"
    RECIBO = "RECIBO"
    TRANSFERENCIA = "TRANSFERENCIA"
    CHEQUE = "CHEQUE"
    PAGARE = "PAGARE"
    LETRA_DE_CAMBIO = "LETRA_DE_CAMBIO"
    JUSTIFICANTE_DE_INGRESO = "JUSTIFICANTE_DE_INGRESO"
    # Contractuales / administrativos
    CONTRATO = "CONTRATO"
    PRESUPUESTO = "PRESUPUESTO"
    ALBARAN = "ALBARAN"
    BUROFAX = "BUROFAX"
    REQUERIMIENTO = "REQUERIMIENTO"
    # Fiscales
    MODELO_303 = "MODELO_303"   # IVA trimestral
    MODELO_130 = "MODELO_130"   # IRPF fraccionado
    MODELO_111 = "MODELO_111"   # retenciones trabajo


# 23 tipos. Dict {valor_str: TipoDocumento} para lookup rápido.
TIPOS_DOCUMENTO: dict[str, TipoDocumento] = {t.value: t for t in TipoDocumento}

# Verificación en import (falla rápido si alguien añade/borra sin actualizar)
assert len(TIPOS_DOCUMENTO) == 23, (
    f"TIPOS_DOCUMENTO debe tener 23 tipos, tiene {len(TIPOS_DOCUMENTO)}"
)