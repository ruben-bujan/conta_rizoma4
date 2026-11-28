# -*- coding: utf-8 -*-
from .modelo import (
    BalanceConsolidado, ConsolidacionError, EliminacionPropuesta,
    RelacionGrupo,
)
from .memoria import (
    BalanceIndividual, EliminacionConsolidacion, EventoConsolidacion, FinalizacionRelacion,
    RelacionParticipacion, RepositorioConsolidacionMemoria,
    ResultadoConsolidacion,
)


def cargar_relaciones(*args, **kwargs):
    """Compatibilidad con el adaptador PostgreSQL heredado (carga diferida)."""
    from .grupo import cargar_relaciones as funcion
    return funcion(*args, **kwargs)


def guardar_relacion(*args, **kwargs):
    """Compatibilidad con el adaptador PostgreSQL heredado (carga diferida)."""
    from .grupo import guardar_relacion as funcion
    return funcion(*args, **kwargs)


def consolidar_grupo(*args, **kwargs):
    """Compatibilidad con el adaptador PostgreSQL heredado (carga diferida)."""
    from .grupo import consolidar_grupo as funcion
    return funcion(*args, **kwargs)

__all__ = [
    'BalanceConsolidado', 'ConsolidacionError', 'EliminacionPropuesta',
    'RelacionGrupo',
    'cargar_relaciones', 'guardar_relacion', 'consolidar_grupo',
    'BalanceIndividual', 'EliminacionConsolidacion', 'EventoConsolidacion', 'FinalizacionRelacion',
    'RelacionParticipacion', 'RepositorioConsolidacionMemoria',
    'ResultadoConsolidacion',
]
