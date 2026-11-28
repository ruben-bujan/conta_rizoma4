# -*- coding: utf-8 -*-
"""Relación administrada entre empresas CONTA y casos investigadores RIZOMA4."""
from __future__ import annotations

import os
import re
from typing import Optional

import psycopg
from psycopg.rows import dict_row

from ..config.postgresql import PG_URL
_PATRON_CASO_ID = re.compile(r"^[A-Za-z0-9_-]+$")


class CasoRizoma4Error(ValueError):
    """Error de validación o relación empresa-caso."""


def validar_caso_id(caso_id: str) -> str:
    valor = caso_id or ""
    if not _PATRON_CASO_ID.fullmatch(valor):
        raise CasoRizoma4Error(
            "caso_id inválido: solo se permiten letras, números, guion y guion bajo"
        )
    return valor


class RepositorioCasoRizoma4:
    """Gestiona asociaciones activables sin borrar el historial de asignaciones."""

    def __init__(self, pg_url: Optional[str] = None):
        self._url = pg_url or PG_URL

    def _conn(self):
        return psycopg.connect(self._url, row_factory=dict_row)

    def listar(self, empresa_id: str, solo_activos: bool = True) -> list[dict]:
        sql = (
            "SELECT empresa_id, caso_id, activo, creado_por, creado_en, "
            "modificado_por, modificado_en, desactivado_en "
            "FROM empresa_casos_rizoma4 WHERE empresa_id = %s"
        )
        if solo_activos:
            sql += " AND activo = TRUE"
        sql += " ORDER BY caso_id"
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, (empresa_id,))
            return cur.fetchall()

    def asociar(self, empresa_id: str, caso_id: str, actor: str) -> dict:
        caso_id = validar_caso_id(caso_id)
        if not empresa_id or not empresa_id.strip():
            raise CasoRizoma4Error("empresa_id es obligatorio")
        if not actor or not actor.strip():
            raise CasoRizoma4Error("actor es obligatorio")
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """INSERT INTO empresa_casos_rizoma4
                   (empresa_id, caso_id, activo, creado_por, modificado_por,
                    creado_en, modificado_en, desactivado_en)
                   VALUES (%s, %s, TRUE, %s, %s, NOW(), NOW(), NULL)
                   ON CONFLICT (empresa_id, caso_id) DO UPDATE SET
                     activo = TRUE,
                     modificado_por = EXCLUDED.modificado_por,
                     modificado_en = NOW(),
                     desactivado_en = NULL
                   RETURNING empresa_id, caso_id, activo, creado_por, creado_en,
                             modificado_por, modificado_en, desactivado_en""",
                (empresa_id, caso_id, actor, actor),
            )
            row = cur.fetchone()
        return row

    def desasociar(self, empresa_id: str, caso_id: str, actor: str) -> Optional[dict]:
        caso_id = validar_caso_id(caso_id)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """UPDATE empresa_casos_rizoma4
                   SET activo = FALSE, modificado_por = %s,
                       modificado_en = NOW(), desactivado_en = NOW()
                   WHERE empresa_id = %s AND caso_id = %s AND activo = TRUE
                   RETURNING empresa_id, caso_id, activo, creado_por, creado_en,
                             modificado_por, modificado_en, desactivado_en""",
                (actor, empresa_id, caso_id),
            )
            return cur.fetchone()

    def esta_asociado(self, empresa_id: str, caso_id: str) -> bool:
        caso_id = validar_caso_id(caso_id)
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """SELECT 1 FROM empresa_casos_rizoma4
                   WHERE empresa_id = %s AND caso_id = %s AND activo = TRUE""",
                (empresa_id, caso_id),
            )
            return cur.fetchone() is not None
