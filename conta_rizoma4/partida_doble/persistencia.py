# -*- coding: utf-8 -*-
"""Persistencia de asientos y lineas en Postgres (multi-empresa)."""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from typing import Optional

import psycopg
from psycopg.errors import UniqueViolation

from .modelo import Asiento, Linea
from .creacion import crear_asiento
from ..operativo.asiento import GENESIS
from ..config.postgresql import PG_URL


def _bloquear_empresa(cur, empresa_id: str) -> None:
    """Serializa altas por empresa, incluidas reversiones concurrentes."""
    cur.execute("SELECT pg_advisory_xact_lock(741521, hashtext(%s))", (empresa_id,))


def _guardar_en_cursor(cur, acto: Asiento, empresa_id: str, caso_id: Optional[str]) -> None:
    cur.execute(
        """
        INSERT INTO asiento_contable
            (indice, fecha, concepto, hash_previo, hash, metadatos, empresa_id, caso_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (empresa_id, indice) DO NOTHING
        RETURNING hash
        """,
        (acto.indice, acto.fecha, acto.concepto, acto.hash_previo, acto.hash,
         json.dumps(acto.metadatos), empresa_id, caso_id),
    )
    row = cur.fetchone()
    if row is None:
        cur.execute(
            "SELECT hash, caso_id FROM asiento_contable WHERE empresa_id = %s AND indice = %s",
            (empresa_id, acto.indice),
        )
        existing = cur.fetchone()
        if existing is None or existing != (acto.hash, caso_id):
            raise UniqueViolation(
                f"Conflicto de integridad en el asiento {acto.indice} de {empresa_id}"
            )
        return

    for linea in acto.lineas:
        cur.execute(
            """
            INSERT INTO linea_asiento
                (asiento_indice, cuenta_pgc, debe_centimos, haber_centimos,
                 parrafo_pgc_id, concepto_linea, empresa_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (acto.indice, linea.cuenta_pgc, linea.debe_centimos,
             linea.haber_centimos, linea.parrafo_pgc_id,
             linea.concepto_linea, empresa_id),
        )


def guardar_asiento(
    acto: Asiento,
    pg_url: Optional[str] = None,
    empresa_id: str = "default",
    caso_id: Optional[str] = None,
) -> None:
    """Inserta el asiento y sus lineas. Idempotente real por (empresa_id, indice).

    Si el asiento ya existe con el MISMO hash, no hace nada (éxito idempotente).
    Si existe con un hash DISTINTO, lanza UniqueViolation (conflicto de datos).
    """
    if not empresa_id or not empresa_id.strip():
        raise ValueError("empresa_id no puede estar vacio")
    
    url = pg_url or PG_URL
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            _bloquear_empresa(cur, empresa_id)
            _guardar_en_cursor(cur, acto, empresa_id, caso_id)
        conn.commit()


def revertir_asiento(
    indice_original: int,
    motivo: str,
    actor: str,
    pg_url: Optional[str] = None,
    empresa_id: str = "default",
) -> int:
    """Crea un asiento de reversión (append-only) en lugar de borrar físicamente.
    
    Retorna el índice del nuevo asiento de reversión.
    """
    if not empresa_id or not empresa_id.strip():
        raise ValueError("empresa_id no puede estar vacio")
    if not motivo or not motivo.strip() or not actor or not actor.strip():
        raise ValueError("motivo y actor son obligatorios para revertir un asiento")
    
    url = pg_url or PG_URL
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            _bloquear_empresa(cur, empresa_id)
            # 1. Obtener datos del asiento original
            cur.execute(
                """
                SELECT indice, fecha, concepto, hash_previo, hash, metadatos, caso_id
                FROM asiento_contable
                WHERE empresa_id = %s AND indice = %s
                """,
                (empresa_id, indice_original)
            )
            original = cur.fetchone()
            if not original:
                raise ValueError(f"No se encontró el asiento {indice_original} para la empresa {empresa_id}")
            
            orig_indice, orig_fecha, orig_concepto, orig_hash_previo, orig_hash, orig_metadatos, caso_id = original

            # 2. Obtener líneas originales
            cur.execute(
                """
                SELECT cuenta_pgc, debe_centimos, haber_centimos, parrafo_pgc_id, concepto_linea
                FROM linea_asiento
                WHERE empresa_id = %s AND asiento_indice = %s
                ORDER BY id ASC
                """,
                (empresa_id, indice_original)
            )
            lineas_originales = cur.fetchall()
            if not lineas_originales:
                raise ValueError(f"El asiento {indice_original} no tiene líneas registradas.")

            # 3. Calcular el nuevo índice (MAX + 1 para esta empresa)
            cur.execute(
                "SELECT COALESCE(MAX(indice), 0) + 1 FROM asiento_contable WHERE empresa_id = %s",
                (empresa_id,)
            )
            nuevo_indice = cur.fetchone()[0]

            # 4. Preparar metadatos y concepto de reversión
            metadatos_reversion = dict(orig_metadatos or {})
            caso_id = caso_id or metadatos_reversion.get("caso_id")
            if caso_id:
                metadatos_reversion["caso_id"] = caso_id
            metadatos_reversion.update({
                "es_reversion": True,
                "reversion_de_indice": indice_original,
                "motivo_reversion": motivo,
                "actor_reversion": actor,
                "fecha_reversion": datetime.now(timezone.utc).isoformat()
            })
            
            nuevo_concepto = f"REVERSIÓN del asiento {indice_original}. Motivo: {motivo}"

            # 5. Construir las líneas invertidas (debe <-> haber)
            lineas_invertidas = tuple(
                Linea(
                    cuenta_pgc=l[0],
                    debe_centimos=l[2],  # Invertir: lo que era haber pasa a debe
                    haber_centimos=l[1], # Invertir: lo que era debe pasa a haber
                    parrafo_pgc_id=l[3],
                    concepto_linea=f"Reversión: {l[4]}" if l[4] else "Reversión"
                )
                for l in lineas_originales
            )

            # 6. hash_previo = hash del asiento anterior por índice (mismo criterio
            #    que el API en routers/asientos.py). La cadena es lineal: enlaza
            #    con el predecesor, NO con el asiento original revertido.
            cur.execute(
                "SELECT hash FROM asiento_contable "
                "WHERE empresa_id = %s AND indice = %s",
                (empresa_id, nuevo_indice - 1),
            )
            fila_prev = cur.fetchone()
            hash_previo = fila_prev[0] if fila_prev else GENESIS

            # 7. Constructor canónico: valida el cuadre y calcula huella + hash reales.
            nuevo_acto = crear_asiento(
                indice=nuevo_indice,
                fecha=date.today(),
                concepto=nuevo_concepto,
                lineas=list(lineas_invertidas),
                hash_previo=hash_previo,
                metadatos=metadatos_reversion,
            )
            _guardar_en_cursor(cur, nuevo_acto, empresa_id, caso_id)
        conn.commit()
        return nuevo_indice


def borrar_asiento(
    indice: int,
    pg_url: Optional[str] = None,
    empresa_id: str = "default",
) -> None:
    """Compatibilidad temporal; el borrado contable está deshabilitado."""
    raise RuntimeError(
        "borrar_asiento está deshabilitado: usa revertir_asiento() para corregir "
        "y conserva las eliminaciones solo en utilidades aisladas de pruebas."
    )
