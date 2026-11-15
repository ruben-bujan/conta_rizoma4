# -*- coding: utf-8 -*-
"""Configuración multi-empresa, severamente restringida."""
from .empresas import (
    ConfigError, ConfigEmpresa, ConfigGrupo,
    cargar_config, get_config, recargar_config, get_empresa,
)
__all__ = [
    "ConfigError", "ConfigEmpresa", "ConfigGrupo",
    "cargar_config", "get_config", "recargar_config", "get_empresa",
]
from .tipos_cambio import (
    TiposCambioError, obtener_tipo_cambio, limpiar_cache,
)
