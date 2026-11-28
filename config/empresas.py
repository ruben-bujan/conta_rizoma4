# conta_rizoma4/config/empresas.py — implementación real (A3)
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

ISO_4217 = {
    "EUR", "USD", "GBP", "CHF", "JPY", "SEK", "NOK", "DKK",
    "PLN", "CZK", "HUF", "CAD", "AUD", "MXN", "BRL", "CNY",
}
ISO_3166_ALPHA2 = re.compile(r"^[A-Z]{2}$")
MMDD = re.compile(r"^(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")
MARCOS_VALIDOS = {"PGC_ES", "NIIF", "US_GAAP"}


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


class ConfigError(Exception):
    """Error de validación en la configuración de empresas."""


def _validar_empresa(raw: dict, marcos: set[str]) -> ConfigEmpresa:
    eid = str(raw.get("empresa_id", "")).strip()
    if not eid:
        raise ConfigError("empresa_id vacío")
    nombre = str(raw.get("nombre", "")).strip()
    if not nombre:
        raise ConfigError(f"{eid}: nombre vacío")
    moneda = str(raw.get("moneda_funcional", "")).strip().upper()
    if moneda not in ISO_4217:
        raise ConfigError(f"{eid}: moneda_funcional {moneda!r} no es ISO 4217")
    marco = str(raw.get("marco_contable", "")).strip()
    if marco not in marcos:
        raise ConfigError(f"{eid}: marco_contable {marco!r} no está definido")
    pais = str(raw.get("pais", "")).strip().upper()
    if not ISO_3166_ALPHA2.match(pais):
        raise ConfigError(f"{eid}: pais {pais!r} no es ISO 3166-1 alpha-2")
    grupo = str(raw.get("grupo", "")).strip()
    if not grupo:
        raise ConfigError(f"{eid}: grupo vacío")
    try:
        p = float(raw.get("participacion_matriz", -1))
    except (TypeError, ValueError):
        raise ConfigError(f"{eid}: participacion_matriz no numérico")
    if not (0.0 <= p <= 100.0):
        raise ConfigError(f"{eid}: participacion_matriz {p} fuera de [0, 100]")
    ej = raw.get("ejercicio_fiscal") or {}
    ini = str(ej.get("inicio", "")).strip()
    fin = str(ej.get("fin", "")).strip()
    if not (MMDD.match(ini) and MMDD.match(fin)):
        raise ConfigError(f"{eid}: ejercicio_fiscal MM-DD inválido ({ini!r}, {fin!r})")
    return ConfigEmpresa(eid, nombre, moneda, marco, pais, grupo, p, ini, fin)


def cargar_config(path: Path) -> dict[str, ConfigEmpresa]:
    """Carga, valida y devuelve {empresa_id: ConfigEmpresa}. Falla si hay error."""
    if not path.is_file():
        raise ConfigError(f"no existe {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ConfigError("el YAML raíz debe ser un mapping")
    marcos = set((raw.get("marcos_contables") or {}).keys())
    if not marcos:
        raise ConfigError("marcos_contables vacío")
    empresas_raw = raw.get("empresas") or []
    if not isinstance(empresas_raw, list) or not empresas_raw:
        raise ConfigError("empresas debe ser una lista no vacía")
    salida: dict[str, ConfigEmpresa] = {}
    for e in empresas_raw:
        cfg = _validar_empresa(e, marcos)
        if cfg.empresa_id in salida:
            raise ConfigError(f"empresa_id duplicado: {cfg.empresa_id}")
        salida[cfg.empresa_id] = cfg
    return salida