# -*- coding: utf-8 -*-
"""Configuración multi-empresa, severamente restringida.

- Fuente única: config/empresas.yaml (versionado en el repo, pero el
  fichero real NO se versiona; solo el .example).
- Se carga al arrancar. Cambios requieren reinicio.
- No hay endpoint para editarlo.
- Validación estricta: si falla, el servicio no arranca.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


class ConfigError(Exception):
    """Error en la configuración de empresas."""


@dataclass(frozen=True)
class ConfigEmpresa:
    empresa_id: str
    nombre: str
    moneda_funcional: str
    marco_contable: str
    pais: str
    grupo: str
    participacion_matriz: float
    ejercicio_inicio: str
    ejercicio_fin: str

    def a_dict(self) -> dict:
        return {
            "empresa_id": self.empresa_id,
            "nombre": self.nombre,
            "moneda_funcional": self.moneda_funcional,
            "marco_contable": self.marco_contable,
            "pais": self.pais,
            "grupo": self.grupo,
            "participacion_matriz": self.participacion_matriz,
            "ejercicio_inicio": self.ejercicio_inicio,
            "ejercicio_fin": self.ejercicio_fin,
        }


@dataclass(frozen=True)
class ConfigGrupo:
    version: int
    moneda_grupo: str
    marco_contable_default: str
    marcos_contables: dict[str, dict]
    empresas: dict[str, ConfigEmpresa]
    tipos_cambio_manuales: dict[str, dict[str, float]]


_MONEDAS_VALIDAS = {
    "EUR", "USD", "GBP", "CHF", "JPY", "CNY", "SEK", "NOK", "DKK",
    "PLN", "CZK", "HUF", "RON", "BGN", "HRK", "RUB", "TRY",
    "BRL", "MXN", "ARS", "CLP", "COP", "PEN", "CAD", "AUD", "NZD",
    "INR", "KRW", "SGD", "HKD", "ZAR", "AED", "SAR",
}


def _validar_moneda(moneda: str, contexto: str) -> None:
    if moneda not in _MONEDAS_VALIDAS:
        raise ConfigError(
            f"{contexto}: moneda '{moneda}' no válida. "
            f"Válidas: {sorted(_MONEDAS_VALIDAS)}"
        )


def _validar_mm_dd(valor: str, contexto: str) -> None:
    import re
    if not re.match(r"^\d{2}-\d{2}$", valor):
        raise ConfigError(
            f"{contexto}: '{valor}' no tiene formato MM-DD"
        )
    mm, dd = int(valor[:2]), int(valor[3:])
    if not (1 <= mm <= 12 and 1 <= dd <= 31):
        raise ConfigError(f"{contexto}: '{valor}' no es fecha válida")


def cargar_config(path: Optional[Path] = None) -> ConfigGrupo:
    """Carga y valida config/empresas.yaml. Falla rápido si hay error."""
    if path is None:
        path = Path(os.environ.get("CONTA_EMPRESAS_YAML", "config/empresas.yaml"))
    if not path.exists():
        raise ConfigError(
            f"No existe {path}. Copia config/empresas.yaml.example "
            f"y adapta."
        )
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: el YAML no es un dict")

    version = data.get("version", 0)
    if version != 1:
        raise ConfigError(f"{path}: version {version} no soportada (solo 1)")

    moneda_grupo = data.get("moneda_grupo", "EUR")
    _validar_moneda(moneda_grupo, "moneda_grupo")

    marco_default = data.get("marco_contable_default", "PGC_ES")
    marcos = data.get("marcos_contables", {})
    if marco_default not in marcos:
        raise ConfigError(
            f"marco_contable_default '{marco_default}' no está en "
            f"marcos_contables"
        )

    empresas_raw = data.get("empresas", [])
    if not empresas_raw:
        raise ConfigError(f"{path}: no hay empresas definidas")

    empresas: dict[str, ConfigEmpresa] = {}
    for i, emp in enumerate(empresas_raw):
        try:
            empresa_id = emp["empresa_id"]
        except KeyError:
            raise ConfigError(f"empresas[{i}]: falta empresa_id")
        if not empresa_id or not empresa_id.strip():
            raise ConfigError(f"empresas[{i}]: empresa_id vacío")
        if empresa_id in empresas:
            raise ConfigError(f"empresa_id duplicado: {empresa_id}")

        _validar_moneda(
            emp.get("moneda_funcional", "EUR"),
            f"empresas[{empresa_id}].moneda_funcional",
        )
        mc = emp.get("marco_contable", marco_default)
        if mc not in marcos:
            raise ConfigError(
                f"empresas[{empresa_id}].marco_contable '{mc}' no está "
                f"en marcos_contables"
            )
        particip = float(emp.get("participacion_matriz", 100.0))
        if not (0.0 <= particip <= 100.0):
            raise ConfigError(
                f"empresas[{empresa_id}].participacion_matriz "
                f"fuera de [0,100]: {particip}"
            )

        ef = emp.get("ejercicio_fiscal", {"inicio": "01-01", "fin": "12-31"})
        _validar_mm_dd(ef.get("inicio", "01-01"), f"empresas[{empresa_id}].inicio")
        _validar_mm_dd(ef.get("fin", "12-31"), f"empresas[{empresa_id}].fin")

        empresas[empresa_id] = ConfigEmpresa(
            empresa_id=empresa_id,
            nombre=emp.get("nombre", empresa_id),
            moneda_funcional=emp.get("moneda_funcional", "EUR"),
            marco_contable=mc,
            pais=emp.get("pais", "ES"),
            grupo=emp.get("grupo", "JV_VECTOR"),
            participacion_matriz=particip,
            ejercicio_inicio=ef.get("inicio", "01-01"),
            ejercicio_fin=ef.get("fin", "12-31"),
        )

    tipos_manuales = data.get("tipos_cambio_manuales", {})
    if not isinstance(tipos_manuales, dict):
        raise ConfigError("tipos_cambio_manuales debe ser dict")

    return ConfigGrupo(
        version=version,
        moneda_grupo=moneda_grupo,
        marco_contable_default=marco_default,
        marcos_contables=marcos,
        empresas=empresas,
        tipos_cambio_manuales=tipos_manuales,
    )


# ─── Cache global (carga perezosa) ────────────────────────────

_cache: Optional[ConfigGrupo] = None


def get_config() -> ConfigGrupo:
    """Devuelve la config cacheada. Carga la primera vez."""
    global _cache
    if _cache is None:
        _cache = cargar_config()
    return _cache


def recargar_config() -> ConfigGrupo:
    """Fuerza recarga. Para tests o reinicio controlado."""
    global _cache
    _cache = None
    return get_config()


def get_empresa(empresa_id: str) -> ConfigEmpresa:
    """Devuelve la config de una empresa. Falla si no existe."""
    cfg = get_config()
    if empresa_id not in cfg.empresas:
        raise ConfigError(
            f"empresa_id '{empresa_id}' no está en config/empresas.yaml. "
            f"Válidas: {sorted(cfg.empresas.keys())}"
        )
    return cfg.empresas[empresa_id]
