"""Pruebas del repositorio formal en memoria."""
from datetime import datetime


def test_repositorio_memoria_guarda_y_recupera():
    from conta_rizoma4.dominio.adaptadores.repositorio_memoria import RepositorioMemoriaDominio
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable
    from conta_rizoma4.dominio import EntidadContable

    nucleo = NucleoEpistemicoContable()
    repositorio = RepositorioMemoriaDominio(nucleo)
    entidad = EntidadContable("EMP-A", "Empresa A")

    repositorio.guardar("ENTIDAD", "EMP-A", entidad)

    assert repositorio.obtener("ENTIDAD", "EMP-A") is entidad


def test_repositorio_memoria_reconstruye_via_nucleo():
    from conta_rizoma4.dominio.adaptadores.repositorio_memoria import RepositorioMemoriaDominio
    from conta_rizoma4.dominio.servicios.nucleo import NucleoEpistemicoContable

    nucleo = NucleoEpistemicoContable()
    repositorio = RepositorioMemoriaDominio(nucleo)

    estado = repositorio.reconstruir(datetime(2025, 4, 18))

    assert estado["eventos_disponibles"] == 0
