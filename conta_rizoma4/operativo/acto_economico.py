# -*- coding: utf-8 -*-
"""Acto económico = asiento con hash encadenado + cadena de mando.

Campos semánticos:  fecha, cuenta_pgc, importe, concepto, A/B/C, párrafo.
Campos de cadena:   indice, huella_contenido, hash_previo, hash.
Campos de mando:    creado_por (obligatorio), validado_por, aprobado_por.
Campos de enlace:   justificacion_indice, cuenta_contrapartida (opcionales).

El importe SIEMPRE es int en céntimos. Nunca float.
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
class ActoEconomico:
    indice: int
    fecha: date
    cuenta_pgc: str
    importe_centimos: int
    concepto: str
    creado_por: str
    huella_contenido: str
    hash_previo: str
    hash: str
    moneda: str = "EUR"
    actividad_nivel: Optional[str] = None
    actividad_id: Optional[int] = None
    interlocutor_tipo: Optional[str] = None
    interlocutor_nif: Optional[str] = None
    documento_tipo: Optional[str] = None
    documento_ref: Optional[str] = None
    parrafo_pgc_id: Optional[int] = None
    validado_por: Optional[str] = None
    aprobado_por: Optional[str] = None
    justificacion_indice: Optional[int] = None
    cuenta_contrapartida: Optional[str] = None
    metadatos: dict[str, Any] = field(default_factory=dict)

    def a_dict(self) -> dict[str, Any]:
        return {
            "indice": self.indice,
            "fecha": self.fecha.isoformat(),
            "cuenta_pgc": self.cuenta_pgc,
            "importe_centimos": self.importe_centimos,
            "moneda": self.moneda,
            "concepto": self.concepto,
            "actividad_nivel": self.actividad_nivel,
            "actividad_id": self.actividad_id,
            "interlocutor_tipo": self.interlocutor_tipo,
            "interlocutor_nif": self.interlocutor_nif,
            "documento_tipo": self.documento_tipo,
            "documento_ref": self.documento_ref,
            "parrafo_pgc_id": self.parrafo_pgc_id,
            "justificacion_indice": self.justificacion_indice,
            "cuenta_contrapartida": self.cuenta_contrapartida,
            "creado_por": self.creado_por,
            "validado_por": self.validado_por,
            "aprobado_por": self.aprobado_por,
            "metadatos": self.metadatos,
            "huella_contenido": self.huella_contenido,
            "hash_previo": self.hash_previo,
            "hash": self.hash,
        }


def crear_acto_economico(
    *,
    indice: int,
    fecha: date,
    cuenta_pgc: str,
    importe_centimos: int,
    concepto: str,
    creado_por: str,
    hash_previo: str = GENESIS,
    moneda: str = "EUR",
    actividad_nivel: Optional[str] = None,
    actividad_id: Optional[int] = None,
    interlocutor_tipo: Optional[str] = None,
    interlocutor_nif: Optional[str] = None,
    documento_tipo: Optional[str] = None,
    documento_ref: Optional[str] = None,
    parrafo_pgc_id: Optional[int] = None,
    validado_por: Optional[str] = None,
    aprobado_por: Optional[str] = None,
    justificacion_indice: Optional[int] = None,
    cuenta_contrapartida: Optional[str] = None,
    metadatos: Optional[dict[str, Any]] = None,
) -> ActoEconomico:
    """Crea el acto, calcula huella y hash encadenado."""
    if not isinstance(importe_centimos, int):
        raise TypeError(
            f"importe_centimos debe ser int, es {type(importe_centimos).__name__}"
        )
    if not creado_por:
        raise ValueError("creado_por es obligatorio (cadena de mando)")

    contenido: dict[str, Any] = {
        "fecha": fecha.isoformat(),
        "cuenta_pgc": cuenta_pgc,
        "importe_centimos": importe_centimos,
        "moneda": moneda,
        "concepto": concepto,
        "actividad_nivel": actividad_nivel,
        "actividad_id": actividad_id,
        "interlocutor_tipo": interlocutor_tipo,
        "interlocutor_nif": interlocutor_nif,
        "documento_tipo": documento_tipo,
        "documento_ref": documento_ref,
        "parrafo_pgc_id": parrafo_pgc_id,
        "creado_por": creado_por,
        "validado_por": validado_por,
        "aprobado_por": aprobado_por,
        "metadatos": metadatos or {},
    }
    # Campos opcionales de enlace: solo entran en la huella si están
    # presentes. Esto preserva la compatibilidad con actos antiguos
    # (creados sin estos campos, con huella calculada sin ellos).
    if justificacion_indice is not None:
        contenido["justificacion_indice"] = justificacion_indice
    if cuenta_contrapartida is not None:
        contenido["cuenta_contrapartida"] = cuenta_contrapartida

    huella = calcular_huella(contenido)
    hash_ = calcular_hash(huella, hash_previo, indice)

    return ActoEconomico(
        indice=indice,
        fecha=fecha,
        cuenta_pgc=cuenta_pgc,
        importe_centimos=importe_centimos,
        concepto=concepto,
        creado_por=creado_por,
        huella_contenido=huella,
        hash_previo=hash_previo,
        hash=hash_,
        moneda=moneda,
        actividad_nivel=actividad_nivel,
        actividad_id=actividad_id,
        interlocutor_tipo=interlocutor_tipo,
        interlocutor_nif=interlocutor_nif,
        documento_tipo=documento_tipo,
        documento_ref=documento_ref,
        parrafo_pgc_id=parrafo_pgc_id,
        validado_por=validado_por,
        aprobado_por=aprobado_por,
        justificacion_indice=justificacion_indice,
        cuenta_contrapartida=cuenta_contrapartida,
        metadatos=metadatos or {},
    )


def guardar_acto_economico(
    acto: ActoEconomico,
    pg_url: Optional[str] = None,
) -> None:
    """Inserta el acto en Postgres. Idempotente por indice."""
    url = pg_url or PG_URL
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO acto_economico (
                    indice, fecha, cuenta_pgc, importe_centimos, moneda,
                    concepto, actividad_nivel, actividad_id,
                    interlocutor_tipo, interlocutor_nif,
                    documento_tipo, documento_ref, parrafo_pgc_id,
                    justificacion_indice, cuenta_contrapartida,
                    creado_por, validado_por, aprobado_por,
                    huella_contenido, hash_previo, hash, metadatos
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s
                )
                ON CONFLICT (indice) DO NOTHING
                """,
                (
                    acto.indice, acto.fecha, acto.cuenta_pgc,
                    acto.importe_centimos, acto.moneda,
                    acto.concepto, acto.actividad_nivel, acto.actividad_id,
                    acto.interlocutor_tipo, acto.interlocutor_nif,
                    acto.documento_tipo, acto.documento_ref,
                    acto.parrafo_pgc_id,
                    acto.justificacion_indice, acto.cuenta_contrapartida,
                    acto.creado_por, acto.validado_por, acto.aprobado_por,
                    acto.huella_contenido, acto.hash_previo, acto.hash,
                    json.dumps(acto.metadatos),
                ),
            )
        conn.commit()


def leer_ultimo_acto(pg_url: Optional[str] = None) -> Optional[dict]:
    """Devuelve el último acto (mayor indice) como dict, o None."""
    url = pg_url or PG_URL
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT indice, hash FROM acto_economico "
                "ORDER BY indice DESC LIMIT 1"
            )
            row = cur.fetchone()
    if row is None:
        return None
    return {"indice": row[0], "hash": row[1]}