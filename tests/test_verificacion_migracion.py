"""Pruebas de importación reversible en memoria."""


def _asientos():
    return [
        {
            "empresa_id": "EMP-A",
            "indice": 1,
            "fecha": "2025-04-12",
            "concepto": "Factura",
            "hash": "ABC123",
        },
        {
            "empresa_id": "EMP-A",
            "indice": 2,
            "fecha": "2025-04-18",
            "concepto": "Cobro",
            "hash": "DEF456",
        },
    ]


def test_importacion_copia_es_reversible():
    from conta_rizoma4.dominio.verificacion_migracion import PruebaMigracionMemoria

    prueba = PruebaMigracionMemoria(_asientos())
    prueba.importar_copia()

    resultado = prueba.verificar()

    assert resultado.reversible
    assert resultado.total_heredado == 2
    assert resultado.total_importado == 2


def test_rollback_descarta_copia():
    from conta_rizoma4.dominio.verificacion_migracion import PruebaMigracionMemoria

    prueba = PruebaMigracionMemoria(_asientos())
    prueba.importar_copia()
    prueba.rollback_logico()

    resultado = prueba.verificar()

    assert resultado.total_heredado == 2
    assert resultado.total_importado == 0
    assert not resultado.reversible


def test_diferencia_detectada():
    from conta_rizoma4.dominio.verificacion_migracion import PruebaMigracionMemoria

    prueba = PruebaMigracionMemoria(_asientos())
    prueba.importar_copia()
    prueba._copia_importada[0]["concepto"] = "Concepto alterado"

    resultado = prueba.verificar()

    diferencias_concepto = [
        diferencia for diferencia in resultado.diferencias
        if diferencia.campo == "concepto"
    ]
    assert len(diferencias_concepto) == 1
