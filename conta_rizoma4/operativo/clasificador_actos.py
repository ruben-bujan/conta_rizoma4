"""Clasificación de asientos por reglas sobre cuentas PGC.

Extraído de importar_inciv_2010.py (M5) para hacerlo testeable.
"""
from __future__ import annotations
from typing import Iterable, Protocol

class Linea(Protocol):
    cuenta_pgc: str

Predicado = "callable[[str, list[str]], bool]"
REGLAS: list[tuple[str, callable]] = [
    ("A_OPERACION_VINCULADA",
     lambda c, cs: any(x.startswith(("551", "552")) for x in cs)),
    ("A_GASTO_BANCARIO",
     lambda c, cs: any(x.startswith("626") for x in cs)),
    ("A_NOMINA",
     lambda c, cs: any(x.startswith("64") for x in cs)),
    ("A_GASTO_GENERAL",
     lambda c, cs: "tarjeta" in c),
    ("A_FACT_RECIBIDA_SERVICIOS",
     lambda c, cs: any(x.startswith("472") for x in cs)
              and any(x.startswith("6") for x in cs)),
    ("A_FACT_EMIT_SERV",
     lambda c, cs: any(x.startswith("477") for x in cs)
              and any(x.startswith("7") for x in cs)),
    ("A_PAGO_PROVEEDOR",
     lambda c, cs: any(x.startswith("572") for x in cs)
              and any(x.startswith(("40", "41")) for x in cs)),
    ("A_COBRO_CLIENTE",
     lambda c, cs: any(x.startswith("572") for x in cs)
              and any(x.startswith("43") for x in cs)),
    ("A_LIQUIDACION_TRIBUTARIA",
     lambda c, cs: any(x.startswith(("475", "477")) for x in cs)),
]

def clasificar_acto(concepto: str, lineas: Iterable[Linea]) -> str:
    c = (concepto or "").lower()
    cuentas = [l.cuenta_pgc for l in lineas]
    for codigo, predicado in REGLAS:
        if predicado(c, cuentas):
            return codigo
    return "A_ASIENTO_GENERAL"