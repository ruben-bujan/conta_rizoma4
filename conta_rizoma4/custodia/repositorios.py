# -*- coding: utf-8 -*-
"""Repositorios de custodia: obras, operarios, leases, documentos."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

import psycopg
from psycopg.rows import dict_row

from .modelo import (
    CustodiaError, Documento, Lease, Obra, Operario,
)


from ..config.postgresql import PG_URL


# ─── Obras ────────────────────────────────────────────────────────

class RepositorioObra:
    def __init__(self, pg_url: Optional[str] = None):
        self._url = pg_url or PG_URL

    def _conn(self):
        return psycopg.connect(self._url, row_factory=dict_row)

    def crear(self, obra: Obra) -> Obra:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO obras
                    (obra_id, empresa_id, nombre, cliente_nif,
                     presupuesto_centimos, fecha_inicio, fecha_fin,
                     estado, config_sync)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (obra_id) DO NOTHING""",
                    (obra.obra_id, obra.empresa_id, obra.nombre,
                     obra.cliente_nif, obra.presupuesto_centimos,
                     obra.fecha_inicio, obra.fecha_fin, obra.estado,
                     psycopg.types.json.Jsonb(obra.config_sync)),
                )
            conn.commit()
        return obra

    def obtener(self, obra_id: str) -> Optional[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM obras WHERE obra_id = %s", (obra_id,))
                return cur.fetchone()

    def listar(self, empresa_id: str) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM obras WHERE empresa_id = %s ORDER BY obra_id",
                    (empresa_id,),
                )
                return cur.fetchall()


# ─── Operarios ────────────────────────────────────────────────────

class RepositorioOperario:
    def __init__(self, pg_url: Optional[str] = None):
        self._url = pg_url or PG_URL

    def _conn(self):
        return psycopg.connect(self._url, row_factory=dict_row)

    def crear(self, op: Operario) -> Operario:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO operarios
                    (operario_id, empresa_id, nombre, rol, email,
                     certificado, activo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (operario_id) DO NOTHING""",
                    (op.operario_id, op.empresa_id, op.nombre, op.rol,
                     op.email, op.certificado, op.activo),
                )
            conn.commit()
        return op

    def obtener(self, operario_id: str) -> Optional[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM operarios WHERE operario_id = %s",
                    (operario_id,),
                )
                return cur.fetchone()

    def listar(self, empresa_id: str) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM operarios WHERE empresa_id = %s ORDER BY operario_id",
                    (empresa_id,),
                )
                return cur.fetchall()


# ─── Leases ───────────────────────────────────────────────────────

class RepositorioLease:
    def __init__(self, pg_url: Optional[str] = None):
        self._url = pg_url or PG_URL

    def _conn(self):
        return psycopg.connect(self._url, row_factory=dict_row)

    def solicitar(
        self, empresa_id: str, obra_id: Optional[str], tipo: str,
        operario: str, duracion_min: int = 1440,
    ) -> dict:
        """Reserva el siguiente índice libre. Devuelve el lease."""
        lease_id = str(uuid.uuid4())
        with self._conn() as conn:
            with conn.cursor() as cur:
                # Serializa la asignación por empresa: sin este bloqueo, dos
                # solicitudes concurrentes podrían reservar el mismo índice.
                cur.execute(
                    "SELECT pg_advisory_xact_lock(741522, hashtext(%s))",
                    (empresa_id,),
                )
                # 1. Siguiente índice libre: mayor que el último usado o reservado
                cur.execute(
                    """SELECT COALESCE(MAX(i), -1) + 1 AS siguiente FROM (
                        SELECT MAX(indice) AS i FROM asiento_contable
                        WHERE empresa_id = %s
                        UNION ALL
                        SELECT MAX(indice_reservado) AS i FROM leases
                        WHERE empresa_id = %s AND estado = 'CONCEDIDO'
                    ) sub""",
                    (empresa_id, empresa_id),
                )
                siguiente = cur.fetchone()["siguiente"]
                expira = datetime.now() + timedelta(minutes=duracion_min)
                cur.execute(
                    """INSERT INTO leases
                    (lease_id, empresa_id, obra_id, tipo, indice_reservado,
                     operario, estado, expira_en)
                    VALUES (%s, %s, %s, %s, %s, %s, 'CONCEDIDO', %s)
                    RETURNING *""",
                    (lease_id, empresa_id, obra_id, tipo, siguiente,
                     operario, expira),
                )
                lease = cur.fetchone()
            conn.commit()
        return lease

    def obtener(self, lease_id: str) -> Optional[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM leases WHERE lease_id = %s", (lease_id,))
                return cur.fetchone()

    def renovar(self, lease_id: str, duracion_min: int = 1440) -> dict:
        with self._conn() as conn:
            with conn.cursor() as cur:
                nueva_expira = datetime.now() + timedelta(minutes=duracion_min)
                cur.execute(
                    """UPDATE leases
                    SET expira_en = %s, renovado_en = NOW()
                    WHERE lease_id = %s AND estado = 'CONCEDIDO'
                    RETURNING *""",
                    (nueva_expira, lease_id),
                )
                lease = cur.fetchone()
                if lease is None:
                    raise CustodiaError(
                        f"Lease {lease_id} no encontrado o no está CONCEDIDO"
                    )
            conn.commit()
        return lease

    def cancelar(self, lease_id: str) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE leases SET estado = 'CANCELADO' WHERE lease_id = %s",
                    (lease_id,),
                )
            conn.commit()

    def marcar_usado(self, lease_id: str) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE leases SET estado = 'USADO', usado_en = NOW() WHERE lease_id = %s",
                    (lease_id,),
                )
            conn.commit()

    def expirar_antiguos(self) -> int:
        """Marca como EXPIRADO los leases caducados. Devuelve cuántos."""
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE leases SET estado = 'EXPIRADO'
                    WHERE estado = 'CONCEDIDO' AND expira_en < NOW()"""
                )
                n = cur.rowcount
            conn.commit()
        return n


# ─── Documentos ───────────────────────────────────────────────────

class RepositorioDocumento:
    def __init__(self, pg_url: Optional[str] = None):
        self._url = pg_url or PG_URL

    def _conn(self):
        return psycopg.connect(self._url, row_factory=dict_row)

    def crear(
        self, empresa_id: str, hash_cas: str, tipo: str,
        obra_id: Optional[str] = None, nombre: Optional[str] = None,
        tamano_bytes: Optional[int] = None,
        subido_por: Optional[str] = None,
    ) -> dict:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO documentos
                    (empresa_id, obra_id, hash_cas, tipo, nombre,
                     tamano_bytes, subido_por)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (empresa_id, hash_cas) DO NOTHING
                    RETURNING *""",
                    (empresa_id, obra_id, hash_cas, tipo, nombre,
                     tamano_bytes, subido_por),
                )
                doc = cur.fetchone()
                if doc is None:
                    cur.execute(
                        "SELECT * FROM documentos WHERE empresa_id = %s AND hash_cas = %s",
                        (empresa_id, hash_cas),
                    )
                    doc = cur.fetchone()
            conn.commit()
        return doc

    def obtener_por_hash(self, empresa_id: str, hash_cas: str) -> Optional[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM documentos WHERE empresa_id = %s AND hash_cas = %s",
                    (empresa_id, hash_cas),
                )
                return cur.fetchone()
