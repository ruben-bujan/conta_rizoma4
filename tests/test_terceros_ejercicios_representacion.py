"""Integración mínima de tercero, movimiento, ejercicio y representación."""
from datetime import datetime


def test_movimiento_y_representacion_en_ejercicio():
    from conta_rizoma4.dominio import (
        EjercicioContable,
        Linea,
        MovimientoEconomico,
        RepresentacionContable,
        Tercero,
    )

    tercero = Tercero(
        tercero_id="T-CLIENTE",
        tipo="JURIDICA",
        nombre="Cliente prueba",
        identificador_fiscal="B12345678",
    )

    movimiento = MovimientoEconomico(
        movimiento_id="M-FACTURA",
        entidad_id="EMP-A",
        tercero_id=tercero.tercero_id,
        tipo="DERECHO_COBRO",
        importe=121000,
        fecha_documental=datetime(2025, 4, 12),
        fecha_vencimiento=datetime(2025, 5, 12),
    )

    ejercicio = EjercicioContable(
        ejercicio_id="E-2025",
        entidad_id="EMP-A",
        inicio=datetime(2025, 1, 1),
        fin=datetime(2025, 12, 31),
    )

    representacion = RepresentacionContable(
        representacion_id="R-1",
        hecho_ids=("H-1",),
        interpretacion_id="I-1",
        decision_id="D-1",
        criterio_ids=("C-1",),
        marco="PGC_ES",
        fecha_contable=movimiento.fecha_documental,
        lineas=(Linea("430", debe=121000), Linea("705", haber=121000)),
        autorizacion_id="A-1",
    )

    assert ejercicio.inicio <= representacion.fecha_contable <= ejercicio.fin
    assert representacion.cuadra()
