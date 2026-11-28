"""Pruebas de exposición pública de migración."""


def test_api_migracion_visible():
    from conta_rizoma4.dominio import (
        CorrespondenciaHeredada,
        ResultadoImportacion,
        crear_correspondencia_asiento,
    )

    correspondencia = crear_correspondencia_asiento(
        "EMP-A", 77, "REP-EMP-A-77"
    )

    assert CorrespondenciaHeredada.__name__ == "CorrespondenciaHeredada"
    assert ResultadoImportacion.__name__ == "ResultadoImportacion"
    assert correspondencia.destino_id == "REP-EMP-A-77"
