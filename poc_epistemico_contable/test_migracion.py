"""Pruebas del plan de migración gradual."""
from .migracion import OBLIGACIONES_DECLARATIVAS, listar_primer_paquete, prioridad


def test_paquete_inicial_contiene_operaciones_base():
    codigos = {item.codigo for item in listar_primer_paquete()}
    assert "A_FACT_EMIT_SERV_NAC_SIN_RET" in codigos
    assert "A_COBRO_CLIENTE_TRANSF" in codigos
    assert "A_PAGO_PROVEEDOR_TRANSF" in codigos


def test_informativos_no_estan_en_paquete_contable():
    codigos = {item.codigo for item in listar_primer_paquete()}
    assert all(codigo not in codigos for codigo in OBLIGACIONES_DECLARATIVAS)


def test_prioridad_rectificaciones_despues_del_vertical_slice():
    assert prioridad("A_FACT_RECT_EMIT") >= 2


def test_cierres_reconocidos_como_diferidos():
    por_codigo = {item.codigo: item for item in listar_primer_paquete()}
    assert por_codigo["A_CIERRE_EJERCICIO"].estrategia == "DIFERIR"
