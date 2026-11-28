"""Pruebas de ejercicios contables formales."""
from datetime import datetime


def test_ejercicio_abierto_valido():
    from conta_rizoma4.dominio import EjercicioContable

    ejercicio = EjercicioContable(
        ejercicio_id="E-2025",
        entidad_id="EMP-A",
        inicio=datetime(2025, 1, 1),
        fin=datetime(2025, 12, 31),
    )

    assert ejercicio.estado == "ABIERTO"


def test_ejercicio_fecha_inversa_falla():
    from conta_rizoma4.dominio import EjercicioContable

    try:
        EjercicioContable(
            ejercicio_id="E-MALO",
            entidad_id="EMP-A",
            inicio=datetime(2025, 12, 31),
            fin=datetime(2025, 1, 1),
        )
    except ValueError:
        return
    raise AssertionError("Fin antes de inicio debe fallar")


def test_fecha_representacion_puede_validarse_en_ejercicio():
    from conta_rizoma4.dominio import EjercicioContable

    ejercicio = EjercicioContable(
        ejercicio_id="E-2025",
        entidad_id="EMP-A",
        inicio=datetime(2025, 1, 1),
        fin=datetime(2025, 12, 31),
    )

    fecha = datetime(2025, 6, 15)

    assert ejercicio.inicio <= fecha <= ejercicio.fin
