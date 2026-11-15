# -*- coding: utf-8 -*-
"""Creación y validación de asientos (partida doble)."""
from __future__ import annotations

from datetime import date
from typing import Any, Optional

from .modelo import Asiento, Linea, PartidaDobleError
from ..operativo.asiento import GENESIS, calcular_hash, calcular_huella


def crear_asiento(
    *,
    indice: int,
    fecha: date,
    concepto: str,
    lineas: list[Linea],
    hash_previo: str = GENESIS,
    metadatos: Optional[dict[str, Any]] = None,
) -> Asiento:
    """Crea un asiento con partida doble.

    Reglas:
      - Al menos 2 líneas.
      - SUM(debe) == SUM(haber).
      - Cada línea: debe>0 XOR haber>0 (validado en Linea).
    """
    if not lineas:
        raise PartidaDobleError("un asiento necesita al menos 2 líneas")
    if len(lineas) < 2:
        raise PartidaDobleError(
            f"un asiento necesita al menos 2 líneas, tiene {len(lineas)}"
        )
    total_debe = sum(l.debe_centimos for l in lineas)
    total_haber = sum(l.haber_centimos for l in lineas)
    if total_debe != total_haber:
        raise PartidaDobleError(
            f"descuadre: debe={total_debe} haber={total_haber} "
            f"diff={total_debe - total_haber}"
        )
    contenido = {
        "fecha": fecha.isoformat(),
        "concepto": concepto,
        "lineas": [
            {
                "cuenta_pgc": l.cuenta_pgc,
                "debe_centimos": l.debe_centimos,
                "haber_centimos": l.haber_centimos,
                "parrafo_pgc_id": l.parrafo_pgc_id,
                "concepto_linea": l.concepto_linea,
            }
            for l in lineas
        ],
        "metadatos": metadatos or {},
    }
    huella = calcular_huella(contenido)
    hash_ = calcular_hash(huella, hash_previo, indice)
    return Asiento(
        indice=indice, fecha=fecha, concepto=concepto,
        lineas=tuple(lineas), hash_previo=hash_previo, hash=hash_,
        huella_contenido=huella, metadatos=metadatos or {},
    )
