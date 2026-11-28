from dataclasses import dataclass
from conta_rizoma4.operativo.clasificador_actos import clasificar_acto

@dataclass
class L: cuenta_pgc: str

def test_operacion_vinculada():
    assert clasificar_acto("pago", [L("551")]) == "A_OPERACION_VINCULADA"

def test_gasto_bancario():
    assert clasificar_acto("comision", [L("626")]) == "A_GASTO_BANCARIO"

def test_nomina():
    assert clasificar_acto("nomina", [L("640"), L("572")]) == "A_NOMINA"

def test_fact_emit_serv():
    assert clasificar_acto("fra venta", [L("477"), L("705")]) == "A_FACT_EMIT_SERV"

def test_pago_proveedor():
    assert clasificar_acto("pago", [L("572"), L("400")]) == "A_PAGO_PROVEEDOR"

def test_generico():
    assert clasificar_acto("x", [L("999")]) == "A_ASIENTO_GENERAL"

def test_tarjeta():
    assert clasificar_acto("cargo tarjeta", [L("999")]) == "A_GASTO_GENERAL"