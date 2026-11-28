"""Pruebas del contrato local de integración con RIZOMA4."""
from datetime import datetime


def test_vinculo_rizoma4_valido():
    from conta_rizoma4.dominio.integracion import VinculoRizoma4, validar_vinculo

    vinculo = VinculoRizoma4(
        entidad_contable_id="EMP-A",
        hecho_id="H-1",
        caso_rizoma4_id="CASO-1",
        creado_en=datetime(2025, 4, 18),
    )

    validar_vinculo(vinculo)
    assert vinculo.caso_rizoma4_id == "CASO-1"


def test_vinculo_sin_entidad_falla():
    from conta_rizoma4.dominio.integracion import VinculoRizoma4, validar_vinculo

    vinculo = VinculoRizoma4(
        entidad_contable_id="",
        hecho_id=None,
        caso_rizoma4_id="CASO-1",
        creado_en=datetime(2025, 4, 18),
    )

    try:
        validar_vinculo(vinculo)
    except ValueError:
        return
    raise AssertionError("Debe rechazar vínculo sin entidad")
