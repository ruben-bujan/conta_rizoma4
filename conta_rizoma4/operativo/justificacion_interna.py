# -*- coding: utf-8 -*-
"""Justificación interna: obra ejecutada pendiente de facturar.

Es el devengo: el trabajo está hecho (o el servicio prestado) pero
todavía no hay factura. Contablemente, se registra en la cuenta
"4308 Clientes, obra ejecutada pendiente de facturar" (o similar).

Cuando llega la factura, se emite un ActoEconomico que la reclasifica.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional

import psycopg

from .asiento import GENESIS, calcular_hash, calcular_huella


PG_URL = os.environ.get(
    "CONTA_PG_URL",
    "postgresql://rizoma:rizoma_dev@localhost:5433/conta_rizoma4",
)


@dataclass(frozen=True)
class JustificacionInterna:
    indice: int
    fecha: date
    cuenta_pgc: str
    importe_centimos: int
    concepto: str
    creado_por: str
    huella_contenido: str
    hash_previo: str
    hash: str
    obra_ref: Optional[str] = None
    contrato_ref: Optional[str] = None
    validado_por: Optional[str] = None
    metadatos: dict[str, Any] = field(default_factory=dict)


def crear_justificacion_interna(
    *,
    indice: int,
    fecha: date,
    cuenta_pgc: str,
    importe_centimos: int,
    concepto: str,
    creado_por: str,
    hash_previo: str = GENESIS,
    obra_ref: Optional[str] = None,
    contrato_ref: Optional[str] = None,
    validado_por: Optional[str] = None,
    metadatos: Optional[dict[str, Any]] = None,
) -> JustificacionInterna:
    if not isinstance(importe_centimos, int):
        raise TypeError("importe_centimos debe ser int")
    if not creado_por:
        raise ValueError("creado_por es obligatorio")

    contenido = {
        "fecha": fecha.isoformat(),
        "cuenta_pgc": cuenta_pgc,
        "importe_centimos": importe_centimos,
        "concepto": concepto,
        "obra_ref": obra_ref,
        "contrato_ref": contrato_ref,
        "creado_por": creado_por,
        "validado_por": validado_por,
        "metadatos": metadatos or {},
    }
    huella = calcular_huella(contenido)
    hash_ = calcular_hash(huella, hash_previo, indice)

    return JustificacionInterna(
        indice=indice,
        fecha=fecha,
        cuenta_pgc=cuenta_pgc,
        importe_centimos=importe_centimos,
        concepto=concepto,
        creado_por=creado_por,
        huella_contenido=huella,
        hash_previo=hash_previo,
        hash=hash_,
        obra_ref=obra_ref,
        contrato_ref=contrato_ref,
        validado_por=validado_por,
        metadatos=metadatos or {},
    )


def guardar_justificacion_interna(
    just: JustificacionInterna,
    pg_url: Optional[str] = None,
) -> None:
    url = pg_url or PG_URL
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO justificacion_interna (
                    indice, fecha, cuenta_pgc, importe_centimos,
                    concepto, obra_ref, contrato_ref,
                    creado_por, validado_por,
                    huella_contenido, hash_previo, hash, metadatos
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s
                )
                ON CONFLICT (indice) DO NOTHING
                """,
                (
                    just.indice, just.fecha, just.cuenta_pgc,
                    just.importe_centimos,
                    just.concepto, just.obra_ref, just.contrato_ref,
                    just.creado_por, just.validado_por,
                    just.huella_contenido, just.hash_previo, just.hash,
                    json.dumps(just.metadatos),
                ),
            )
        conn.commit()