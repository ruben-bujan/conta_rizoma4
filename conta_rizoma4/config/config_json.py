# -*- coding: utf-8 -*-
"""Configuración segmentada (admin/user) cargada desde JSON."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

_DEFAULT_PATH = os.environ.get("CONTA_CONFIG_JSON", "config/conta_config.json")


def cargar_config(path: str = _DEFAULT_PATH) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        # fallback al example
        alt = Path(str(p) + ".example")
        if alt.exists():
            p = alt
        else:
            return {"admin": {}, "user": {}, "visado": {}}
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def admin(cfg: Dict[str, Any] = None) -> Dict[str, Any]:
    cfg = cfg or cargar_config()
    return cfg.get("admin", {})


def user(cfg: Dict[str, Any] = None) -> Dict[str, Any]:
    cfg = cfg or cargar_config()
    return cfg.get("user", {})
