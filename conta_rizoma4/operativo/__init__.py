# -*- coding: utf-8 -*-
"""Capa operativa de conta-rizoma4."""

from .asiento import (
    GENESIS,
    calcular_hash,
    calcular_huella,
)
from .parrafo_pgc import (
    buscar_parrafo_pgc,
    buscar_parrafos_por_cuenta,
)
from .mapeo_abcd import (
    CUENTA_FALLBACK,
    REGLAS_DEFAULT,
    SugerenciaCuenta,
    sugerir_cuenta_pgc,
)
from .acto_economico import (
    ActoEconomico,
    crear_acto_economico,
    guardar_acto_economico,
    leer_ultimo_acto,
)
from .justificacion_interna import (
    JustificacionInterna,
    crear_justificacion_interna,
    guardar_justificacion_interna,
)
from .repositorio_acto import (
    ReporteCadena,
    RepositorioActoEconomico,
)
from .reclasificacion import (
    CUENTA_DESTINO_DEFAULT,
    CUENTA_ORIGEN_DEFAULT,
    ReclasificacionError,
    justificaciones_pendientes,
    justificaciones_reclasificadas,
    reclasificar_justificacion,
)

__all__ = [
    "GENESIS", "calcular_hash", "calcular_huella",
    "buscar_parrafo_pgc", "buscar_parrafos_por_cuenta",
    "CUENTA_FALLBACK", "REGLAS_DEFAULT", "SugerenciaCuenta",
    "sugerir_cuenta_pgc",
    "ActoEconomico", "crear_acto_economico",
    "guardar_acto_economico", "leer_ultimo_acto",
    "JustificacionInterna", "crear_justificacion_interna",
    "guardar_justificacion_interna",
    "ReporteCadena", "RepositorioActoEconomico",
    "CUENTA_DESTINO_DEFAULT", "CUENTA_ORIGEN_DEFAULT",
    "ReclasificacionError", "justificaciones_pendientes",
    "justificaciones_reclasificadas", "reclasificar_justificacion",
]