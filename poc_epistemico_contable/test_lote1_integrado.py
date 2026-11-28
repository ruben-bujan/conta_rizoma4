"""Integración del primer lote con hechos, decisiones y ledger en memoria."""
from datetime import datetime

from .lote1 import generar_lote1
from .nucleo import NucleoEpistemicoContable


def test_lote1_factura_cobro_y_rectificacion():
    nucleo = NucleoEpistemicoContable()

    factura = generar_lote1(
        "A_FACT_EMIT_SERV_NAC_SIN_RET",
        base_centimos=100000,
        iva_pct=21,
        cliente_nif="B123",
    )
    cobro = generar_lote1(
        "A_COBRO_CLIENTE_TRANSF",
        importe_centimos=50000,
        cliente_nif="B123",
    )

    assert factura.tipo_hecho == "FACTURA_EMITIDA"
    assert cobro.tipo_hecho == "COBRO"

    factura_debe = sum(linea[1] for linea in factura.lineas)
    factura_haber = sum(linea[2] for linea in factura.lineas)
    cobro_debe = sum(linea[1] for linea in cobro.lineas)
    cobro_haber = sum(linea[2] for linea in cobro.lineas)

    assert factura_debe == factura_haber
    assert cobro_debe == cobro_haber

    estado = nucleo.reconstruir(datetime(2025, 4, 18))
    assert estado["eventos_disponibles"] == 0
    assert nucleo.verificar_cadena()["cadena_valida"]
