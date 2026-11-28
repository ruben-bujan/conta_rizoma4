"""Pruebas de casos de uso independientes de infraestructura."""
from datetime import datetime

from .casos_uso import ReconstruirEstado
from .nucleo import NucleoEpistemicoContable
from .repositorio_memoria import RepositorioMemoria


def test_repositorio_memoria_delega_reconstruccion():
    nucleo = NucleoEpistemicoContable()
    repositorio = RepositorioMemoria(nucleo)

    estado = repositorio.reconstruir(datetime(2025, 4, 18))

    assert estado["fecha_epistemica"] == "2025-04-18T00:00:00"
    assert estado["eventos_disponibles"] == 0


def test_caso_uso_reconstruir():
    nucleo = NucleoEpistemicoContable()
    caso = ReconstruirEstado(nucleo)

    estado = caso.ejecutar(datetime(2025, 4, 18))

    assert estado["evidencias"] == {}
    assert estado["decisiones"] == {}
