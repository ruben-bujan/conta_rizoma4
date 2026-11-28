"""Pruebas conceptuales de correspondencia migrada sin pérdida histórica."""


def test_correspondencia_asiento_heredado():
    from conta_rizoma4.dominio.migracion import crear_correspondencia_asiento

    correspondencia = crear_correspondencia_asiento(
        "EMP-A",
        42,
        "REP-EMP-A-42",
    )

    assert correspondencia.origen_tipo == "ASIENTO_CONTABLE_HEREDADO"
    assert correspondencia.origen_empresa == "EMP-A"
    assert correspondencia.origen_indice == 42
    assert correspondencia.destino_id == "REP-EMP-A-42"
    assert "EPSTEMICA" in correspondencia.estado_migracion


def test_correspondencia_no_ejerce_acreditacion():
    from conta_rizoma4.dominio.migracion import crear_correspondencia_asiento

    correspondencia = crear_correspondencia_asiento(
        "EMP-A",
        43,
        "REP-EMP-A-43",
        observaciones=("Sin hecho económico verificable",),
    )

    assert "Sin hecho económico verificable" in correspondencia.observaciones
