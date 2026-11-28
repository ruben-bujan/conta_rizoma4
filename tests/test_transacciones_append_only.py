"""Pruebas conceptuales de transacciones append-only."""
from datetime import datetime


def test_transaccion_append_only_valida():
    from conta_rizoma4.dominio.transacciones import (
        OperacionAppendOnly,
        TransaccionAppendOnly,
        validar_transaccion_append_only,
    )

    operacion = OperacionAppendOnly(
        tipo="HECHO_REGISTRADO",
        entidad_id="EMP-A",
        objeto_tipo="HECHO",
        objeto_id="H-1",
        actor_id="CONTADOR",
        timestamp=datetime(2025, 4, 18),
        motivo="Registro",
    )
    transaccion = TransaccionAppendOnly(
        transaccion_id="TX-1",
        entidad_id="EMP-A",
        operaciones=(operacion,),
        precondiciones=("HECHO_NO_EXISTE",),
        motivo_global="Alta inicial",
    )

    validar_transaccion_append_only(transaccion)


def test_transaccion_sin_operaciones_falla():
    from conta_rizoma4.dominio.transacciones import (
        TransaccionAppendOnly,
        validar_transaccion_append_only,
    )

    transaccion = TransaccionAppendOnly(
        transaccion_id="TX-2",
        entidad_id="EMP-A",
        operaciones=(),
        precondiciones=("NINGUNA",),
        motivo_global="Vacía",
    )

    try:
        validar_transaccion_append_only(transaccion)
    except ValueError:
        return
    raise AssertionError("Debe rechazar transacción sin operaciones")


def test_transaccion_multiempresa_falla():
    from datetime import datetime
    from conta_rizoma4.dominio.transacciones import (
        OperacionAppendOnly,
        TransaccionAppendOnly,
        validar_transaccion_append_only,
    )

    operaciones = (
        OperacionAppendOnly("A", "EMP-A", "HECHO", "H-1", "ACTOR", datetime(2025, 4, 18), "Alta"),
        OperacionAppendOnly("B", "EMP-B", "HECHO", "H-2", "ACTOR", datetime(2025, 4, 18), "Alta"),
    )
    transaccion = TransaccionAppendOnly(
        transaccion_id="TX-3",
        entidad_id="EMP-A",
        operaciones=operaciones,
        precondiciones=("NINGUNA",),
        motivo_global="Operación cruzada",
    )

    try:
        validar_transaccion_append_only(transaccion)
    except ValueError:
        return
    raise AssertionError("Debe rechazar transacción entre empresas")
