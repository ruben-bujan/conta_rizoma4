"""Pruebas del primer lote de migración contable."""
from .lote1 import generar_lote1, REGISTRO_LOTE1


def _cuadra(resultado) -> bool:
    debe = sum(linea[1] for linea in resultado.lineas)
    haber = sum(linea[2] for linea in resultado.lineas)
    return debe == haber


def test_factura_emitida_cuadra():
    resultado = generar_lote1(
        "A_FACT_EMIT_SERV_NAC_SIN_RET",
        base_centimos=100000,
        iva_pct=21,
        cliente_nif="B123",
    )
    assert resultado.tipo_hecho == "FACTURA_EMITIDA"
    assert _cuadra(resultado)


def test_factura_emitida_con_retencion_cuadra():
    resultado = generar_lote1(
        "A_FACT_EMIT_SERV_NAC_CON_RET",
        base_centimos=100000,
        iva_pct=21,
        retencion_pct=15,
    )
    assert _cuadra(resultado)


def test_factura_recibida_cuadra():
    resultado = generar_lote1(
        "A_FACT_REC_GASTO_NAC",
        base_centimos=50000,
        iva_pct=21,
        cuenta_gasto="629",
    )
    assert _cuadra(resultado)


def test_cobro_y_pago_cuadran():
    cobro = generar_lote1("A_COBRO_CLIENTE_TRANSF", importe_centimos=50000)
    pago = generar_lote1("A_PAGO_PROVEEDOR_TRANSF", importe_centimos=40000)
    assert _cuadra(cobro)
    assert _cuadra(pago)


def test_anticipo_se_modela_438():
    resultado = generar_lote1(
        "A_ANTICIPO_CLIENTE",
        importe_centimos=30000,
    )
    cuentas = {linea[0] for linea in resultado.lineas}
    assert "438" in cuentas
    assert _cuadra(resultado)


def test_primer_lote_tiene_seis_registros():
    assert len(REGISTRO_LOTE1) == 6
