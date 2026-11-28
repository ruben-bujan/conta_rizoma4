"""Pruebas de cobros, pagos y anticipos."""
from datetime import datetime


def _ejercicio():
    from conta_rizoma4.dominio import EjercicioContable
    return EjercicioContable(
        ejercicio_id="E-2025",
        entidad_id="EMP-A",
        inicio=datetime(2025, 1, 1),
        fin=datetime(2025, 12, 31),
    )


def test_cobro_cuadra():
    from conta_rizoma4.dominio import Tercero
    from conta_rizoma4.dominio.casos_uso.tesoreria import registrar_cobro

    movimiento, representacion = registrar_cobro(
        entidad_id="EMP-A",
        tercero=Tercero("T-1", "JURIDICA", "Cliente"),
        ejercicio=_ejercicio(),
        hecho_ids=("H-COBRO",),
        interpretacion_id="I-COBRO",
        decision_id="D-COBRO",
        criterio_ids=("C-1",),
        autorizacion_id="A-1",
        representacion_id="R-COBRO",
        fecha=datetime(2025, 4, 18),
        importe_centimos=50000,
        movimiento_id="M-COBRO",
    )

    assert movimiento.tipo == "COBRO"
    assert representacion.cuadra()


def test_pago_cuadra():
    from conta_rizoma4.dominio import Tercero
    from conta_rizoma4.dominio.casos_uso.tesoreria import registrar_pago

    movimiento, representacion = registrar_pago(
        entidad_id="EMP-A",
        tercero=Tercero("T-2", "JURIDICA", "Proveedor"),
        ejercicio=_ejercicio(),
        hecho_ids=("H-PAGO",),
        interpretacion_id="I-PAGO",
        decision_id="D-PAGO",
        criterio_ids=("C-1",),
        autorizacion_id="A-1",
        representacion_id="R-PAGO",
        fecha=datetime(2025, 4, 18),
        importe_centimos=40000,
        movimiento_id="M-PAGO",
    )

    assert movimiento.tipo == "PAGO"
    assert representacion.cuadra()


def test_anticipo_cuadra():
    from conta_rizoma4.dominio import Tercero
    from conta_rizoma4.dominio.casos_uso.tesoreria import registrar_anticipo_cliente

    movimiento, representacion = registrar_anticipo_cliente(
        entidad_id="EMP-A",
        tercero=Tercero("T-1", "JURIDICA", "Cliente"),
        ejercicio=_ejercicio(),
        hecho_ids=("H-ANTICIPO",),
        interpretacion_id="I-ANTICIPO",
        decision_id="D-ANTICIPO",
        criterio_ids=("C-1",),
        autorizacion_id="A-1",
        representacion_id="R-ANTICIPO",
        fecha=datetime(2025, 4, 18),
        importe_centimos=30000,
        movimiento_id="M-ANTICIPO",
    )

    assert movimiento.tipo == "ANTICIPO_CLIENTE"
    assert representacion.cuadra()
