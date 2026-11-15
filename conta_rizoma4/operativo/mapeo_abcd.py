# -*- coding: utf-8 -*-
"""Sugeridor A+B+C→D con justificación doctrinal.

Entrada:  A (actividad), B (interlocutor), C (documento)
Salida:   D (cuenta PGC) + párrafo del PGC que la justifica + motivo

Reglas en cascada:
  1. (doc, interlocutor, actividad) exacto
  2. (doc, interlocutor, None)
  3. (doc, None, None)
  4. Fallback "555" (Partidas pendientes de aplicación)

Las reglas son conservadoras. El operador puede sobrescribirlas.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..contratos import (
    CuentaPGC,
    cargar_cuentas_pgc,
)
from .parrafo_pgc import buscar_parrafo_pgc


# Reglas por defecto. Clave: (documento_tipo, interlocutor_tipo, actividad_nivel1)
# None = comodín. Valor: código de cuenta PGC.
REGLAS_DEFAULT: dict[tuple[Optional[str], Optional[str], Optional[str]], str] = {
    # Facturación
    ("FACTURA_EMITIDA", "JURIDICA", None): "705",   # Prestación de servicios
    ("FACTURA_EMITIDA", "FISICA", None): "705",
    ("FACTURA_RECIBIDA", "JURIDICA", None): "629",  # Otros servicios
    ("FACTURA_RECIBIDA", "FISICA", None): "629",
    ("FACTURA_EMITIDA", None, None): "705",   # genérica (sin interlocutor)
    ("FACTURA_RECIBIDA", None, None): "629",  # genérica (sin interlocutor)
    ("FACTURA_RECTIFICATIVA_EMITIDA", None, None): "708",  # Devoluciones
    ("FACTURA_RECTIFICATIVA_RECIBIDA", None, None): "608",
    # Nóminas
    ("NOMINA", None, None): "640",                  # Sueldos y salarios
    # Bancarios
    ("EXTRACTO_BANCARIO", None, None): "572",       # Bancos
    ("RECIBO", None, None): "572",
    ("TRANSFERENCIA", None, None): "572",
    ("CHEQUE", None, None): "572",
    ("PAGARE", None, None): "572",
    ("LETRA_DE_CAMBIO", None, None): "572",
    ("JUSTIFICANTE_DE_INGRESO", None, None): "572",
    # Contractuales / administrativos
    ("CONTRATO", None, None): "555",                # pendiente de clasificar
    ("PRESUPUESTO", None, None): "555",
    ("ALBARAN", None, None): "555",
    ("BUROFAX", None, None): "555",
    ("REQUERIMIENTO", None, None): "555",
    # Fiscales
    ("MODELO_303", None, None): "472",              # HP IVA soportado
    ("MODELO_130", None, None): "473",              # HP retenciones
    ("MODELO_111", None, None): "4751",             # HP acreedora retenciones
}


CUENTA_FALLBACK = "555"  # Partidas pendientes de aplicación


@dataclass(frozen=True)
class SugerenciaCuenta:
    cuenta: CuentaPGC
    parrafo_pgc: Optional[dict]
    motivo: str
    confianza: float  # 0.0 - 1.0


def sugerir_cuenta_pgc(
    documento_tipo: str,
    interlocutor_tipo: Optional[str] = None,
    actividad_nivel1: Optional[str] = None,
    pg_url: Optional[str] = None,
) -> SugerenciaCuenta:
    """Sugiere la cuenta PGC (D) dado A+B+C.

    Si no hay regla exacta, baja en cascada. Si no hay nada, 555 con
    confianza baja (el operador decide).
    """
    cuenta_str, confianza, motivo = _resolver_cuenta(
        documento_tipo, interlocutor_tipo, actividad_nivel1,
    )
    cuentas = cargar_cuentas_pgc(pg_url=pg_url)
    cuenta = cuentas.get(cuenta_str)
    if cuenta is None:
        # La cuenta configurada no existe en el PGC: caer al fallback
        cuenta = cuentas.get(CUENTA_FALLBACK)
        if cuenta is None:
            raise RuntimeError(
                f"Ni {cuenta_str} ni {CUENTA_FALLBACK} existen en pgc_cuenta"
            )
        motivo = f"{motivo} (cuenta {cuenta_str} inexistente, fallback)"
        confianza = 0.2
    parrafo = buscar_parrafo_pgc(
        cuenta.cuenta, cuenta.descripcion, pg_url=pg_url,
    )
    return SugerenciaCuenta(
        cuenta=cuenta,
        parrafo_pgc=parrafo,
        motivo=motivo,
        confianza=confianza,
    )


def _resolver_cuenta(
    documento_tipo: str,
    interlocutor_tipo: Optional[str],
    actividad_nivel1: Optional[str],
) -> tuple[str, float, str]:
    """Cascada de reglas. Devuelve (cuenta, confianza, motivo).

    Nivel 1: los 3 args no-None y el triple está en REGLAS_DEFAULT → 1.0
    Nivel 2: doc + interlocutor (actividad None)                  → 0.8
    Nivel 3: doc solo (interlocutor None)                         → 0.6
    Fallback: 555 con 0.2
    """
    # Nivel 1: exacto, los 3 no-None
    if (
        actividad_nivel1 is not None
        and interlocutor_tipo is not None
    ):
        clave = (documento_tipo, interlocutor_tipo, actividad_nivel1)
        if clave in REGLAS_DEFAULT:
            return REGLAS_DEFAULT[clave], 1.0, f"regla exacta {clave}"

    # Nivel 2: doc + interlocutor (actividad wildcard)
    if interlocutor_tipo is not None:
        clave2 = (documento_tipo, interlocutor_tipo, None)
        if clave2 in REGLAS_DEFAULT:
            return REGLAS_DEFAULT[clave2], 0.8, f"regla por doc+interlocutor {clave2}"

    # Nivel 3: doc solo
    clave3 = (documento_tipo, None, None)
    if clave3 in REGLAS_DEFAULT:
        return REGLAS_DEFAULT[clave3], 0.6, f"regla por documento {clave3}"

    # Fallback
    return CUENTA_FALLBACK, 0.2, f"sin regla para doc={documento_tipo}"