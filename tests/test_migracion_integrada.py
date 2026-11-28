"""Migración integrada en memoria entre legado y dominio."""
from datetime import datetime


def test_correspondencia_y_repositorio_integrados():
    from conta_rizoma4.dominio import (
        EntidadContable,
        NucleoEpistemicoContable,
        RepositorioMemoriaDominio,
        crear_correspondencia_asiento,
    )

    nucleo = NucleoEpistemicoContable()
    repositorio = RepositorioMemoriaDominio(nucleo)
    entidad = EntidadContable("EMP-A", "Empresa A")

    correspondencia = crear_correspondencia_asiento(
        "EMP-A",
        77,
        "REP-EMP-A-77",
        observaciones=("Datos heredados sin interpretación epistémica",),
    )

    repositorio.guardar("ENTIDAD", entidad.entidad_id, entidad)
    repositorio.guardar("CORRESPONDENCIA", correspondencia.destino_id, correspondencia)

    recuperada = repositorio.obtener("CORRESPONDENCIA", "REP-EMP-A-77")
    reconstruccion = repositorio.reconstruir(datetime(2025, 4, 18))

    assert recuperada is correspondencia
    assert reconstruccion["eventos_disponibles"] == 0


def test_importacion_heredada_no_genera_hecho_acreditado():
    from conta_rizoma4.dominio import crear_correspondencia_asiento

    correspondencia = crear_correspondencia_asiento(
        "EMP-A",
        78,
        "REP-EMP-A-78",
    )

    assert correspondencia.estado_migracion == "IMPORTADO_SIN_ACREDITACION_EPSTEMICA"
