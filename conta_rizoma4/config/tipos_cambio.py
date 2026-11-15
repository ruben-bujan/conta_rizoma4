# -*- coding: utf-8 -*-
"""Tipos de cambio: BCE automático + cache + fallback manual.

Estrategia:
  1. Buscar en la tabla `tipos_cambio` (Postgres).
  2. Si no está, buscar en `config/cache/tipos_cambio_YYYY-MM-DD.json`.
  3. Si no está, descargar del BCE (XML diario).
  4. Si no está, buscar en `config/empresas.yaml` (manuales).
  5. Si no está, error.

La API del BCE:
  https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
  (todos los días laborables, actualizado a las 16:00 CET)

Formato: 1 EUR = X moneda. Para pares EUR_XXX, la tasa es directa.
Para pares XXX_EUR, la tasa es 1/X.
"""
from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from .empresas import get_config


URL_BCE_DIARIO = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
CACHE_DIR = Path(os.environ.get("CONTA_CACHE_DIR", "config/cache"))


class TiposCambioError(Exception):
    """Error al obtener un tipo de cambio."""


# ─── Parseo del XML del BCE ────────────────────────────────────

def _parsear_bce_xml(xml_bytes: bytes) -> tuple[date, dict[str, float]]:
    """Devuelve (fecha, {moneda: tasa_vs_EUR}).

    El BCE publica: 1 EUR = tasa * moneda.
    """
    NS = {
        "gesmes": "http://www.gesmes.org/xml/2002-08-01",
        "eurofxref": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref",
    }
    root = ET.fromstring(xml_bytes)
    cube = root.find("eurofxref:Cube/eurofxref:Cube", NS)
    if cube is None:
        raise TiposCambioError("XML del BCE sin nodo Cube")
    fecha_str = cube.get("time")
    if not fecha_str:
        raise TiposCambioError("XML del BCE sin atributo 'time'")
    fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    tasas = {"EUR": 1.0}
    for child in cube:
        moneda = child.get("currency")
        tasa_str = child.get("rate")
        if moneda and tasa_str:
            tasas[moneda] = float(tasa_str)
    return fecha, tasas


# ─── Cache en disco ────────────────────────────────────────────

def _cache_path(fecha: date) -> Path:
    return CACHE_DIR / f"tipos_cambio_{fecha.isoformat()}.json"


def _leer_cache(fecha: date) -> Optional[dict[str, float]]:
    p = _cache_path(fecha)
    if not p.exists():
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _escribir_cache(fecha: date, tasas: dict[str, float]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(_cache_path(fecha), "w", encoding="utf-8") as f:
        json.dump(tasas, f, indent=2, sort_keys=True)


# ─── Descarga del BCE ─────────────────────────────────────────

def _descargar_bce() -> tuple[date, dict[str, float]]:
    """Descarga el XML diario del BCE y devuelve (fecha, tasas)."""
    import httpx
    try:
        r = httpx.get(URL_BCE_DIARIO, timeout=10.0)
        r.raise_for_status()
    except Exception as e:
        raise TiposCambioError(f"Error descargando BCE: {e}")
    return _parsear_bce_xml(r.content)


# ─── API pública ──────────────────────────────────────────────

def _normalizar_par(par: str) -> str:
    """'EUR_USD' → 'EUR_USD'. Valida."""
    if "_" not in par or len(par) != 7:
        raise TiposCambioError(f"par inválido: {par} (formato XXX_YYY)")
    return par.upper()


def _calcular_tasa(par: str, tasas: dict[str, float]) -> float:
    """Calcula el tipo de cambio para el par a partir de las tasas BCE."""
    base, cotizada = par.split("_")
    if base not in tasas:
        raise TiposCambioError(f"BCE no publica tasa para {base}")
    if cotizada not in tasas:
        raise TiposCambioError(f"BCE no publica tasa para {cotizada}")
    return tasas[base] / tasas[cotizada]


def obtener_tipo_cambio(fecha: date, par: str) -> float:
    """Devuelve el tipo de cambio de `par` en `fecha`.

    Orden:
      1. YAML manuales
      2. Cache en disco (día laborable)
      3. Descarga BCE (solo si fecha es hoy o ayer)
      4. Error
    """
    par = _normalizar_par(par)

    # 1. Manual
    cfg = get_config()
    manuales = cfg.tipos_cambio_manuales.get(fecha.isoformat(), {})
    if par in manuales:
        return float(manuales[par])

    # 2. Cache
    tasas_cache = _leer_cache(fecha)
    if tasas_cache:
        return _calcular_tasa(par, tasas_cache)

    # 3. Descarga BCE (solo si fecha es reciente)
    hoy = date.today()
    if abs((fecha - hoy).days) <= 5:
        fecha_bce, tasas = _descargar_bce()
        _escribir_cache(fecha_bce, tasas)
        if fecha == fecha_bce:
            return _calcular_tasa(par, tasas)
        # Si el BCE ha publicado hoy pero pedimos ayer (fin de semana),
        # usar la última publicada.
        return _calcular_tasa(par, tasas)

    raise TiposCambioError(
        f"Sin tipo de cambio para {par} el {fecha}. "
        f"Añádelo a tipos_cambio_manuales en config/empresas.yaml "
        f"o importa el histórico del BCE."
    )


def limpiar_cache(antes_de: Optional[date] = None) -> int:
    """Borra cache. Devuelve número de ficheros borrados."""
    if not CACHE_DIR.exists():
        return 0
    borrados = 0
    for p in CACHE_DIR.glob("tipos_cambio_*.json"):
        if antes_de is None:
            p.unlink()
            borrados += 1
        else:
            fecha_str = p.stem.replace("tipos_cambio_", "")
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except ValueError:
                continue
            if fecha < antes_de:
                p.unlink()
                borrados += 1
    return borrados
