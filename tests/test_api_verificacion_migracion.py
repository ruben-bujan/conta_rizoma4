"""Pruebas de la API pública de verificación reversible."""


def test_api_verificacion_migracion_visible():
    from conta_rizoma4.dominio import (
        PruebaMigracionMemoria,
        ResultadoVerificacionMigracion,
        verificar_conjunto,
    )

    prueba, resultado = verificar_conjunto([
        {"empresa_id": "EMP-A", "indice": 1, "hash": "ABC"},
    ])

    assert isinstance(prueba, PruebaMigracionMemoria)
    assert isinstance(resultado, ResultadoVerificacionMigracion)
