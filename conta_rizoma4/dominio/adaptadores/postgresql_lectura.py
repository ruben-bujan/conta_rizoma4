"""Adaptador PostgreSQL de sólo lectura para el dominio.

Este módulo no crea, modifica ni elimina datos. Las operaciones disponibles
limitan expresamente su SQL a SELECT y verifican la sentencia antes de ejecutar.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional


class EscrituraProhibidaError(RuntimeError):
    """Se lanza si se intenta ejecutar SQL distinto de lectura."""


_READ_ONLY_PREFIXES = (
    "SELECT ",
    "WITH ",
)


def validar_sql_lectura(sql: str) -> str:
    normalizado = " ".join(sql.strip().upper().split())
    if not normalizado:
        raise EscrituraProhibidaError("SQL vacío no permitido")
    if not normalizado.startswith(_READ_ONLY_PREFIXES):
        raise EscrituraProhibidaError("Sólo se permiten consultas SELECT o WITH")

    prohibidas = (
        r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bDROP\b",
        r"\bALTER\b", r"\bCREATE\b", r"\bTRUNCATE\b", r"\bCALL\b",
        r"\bCOPY\b", r"\bGRANT\b", r"\bREVOKE\b",
    )
    for patron in prohibidas:
        if re.search(patron, normalizado):
            raise EscrituraProhibidaError(
                "La sentencia contiene una operación que no es de lectura"
            )
    return sql


class RepositorioPostgresLectura:
    """Adaptador mínimo de lectura. No posee método guardar ni ejecutar DML."""

    def __init__(self, pg_url: Optional[str] = None) -> None:
        self._pg_url = pg_url

    def _ejecutar_select(self, sql: str, parametros: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        consulta = validar_sql_lectura(sql)

        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError(
                "El adaptador requiere psycopg y no debe usarse para escritura"
            ) from exc

        if not self._pg_url:
            raise RuntimeError("Se requiere una URL PostgreSQL explícita")

        with psycopg.connect(self._pg_url, row_factory=dict_row) as conexion:
            with conexion.transaction():
                conexion.execute("SET TRANSACTION READ ONLY")
                with conexion.cursor() as cursor:
                    cursor.execute(consulta, parametros)
                    return cursor.fetchall()

    def obtener_hecho(self, entidad_id: str, hecho_id: str) -> Optional[dict[str, Any]]:
        filas = self._ejecutar_select(
            """
            SELECT entidad_id, hecho_id, tipo, descripcion,
                   estado_economico, estado_epistemologico,
                   ocurrido_inicio, ocurrido_fin, precision_temporal,
                   conocido_en, registrado_en, incertidumbre,
                   magnitudes, metadatos
            FROM dominio_hecho
            WHERE entidad_id = %s AND hecho_id = %s
            """,
            (entidad_id, hecho_id),
        )
        return filas[0] if filas else None

    def listar_hechos(
        self,
        entidad_id: str,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
    ) -> list[dict[str, Any]]:
        condiciones = ["entidad_id = %s"]
        parametros: list[Any] = [entidad_id]

        if fecha_desde is not None:
            condiciones.append("registrado_en >= %s")
            parametros.append(fecha_desde)

        if fecha_hasta is not None:
            condiciones.append("registrado_en <= %s")
            parametros.append(fecha_hasta)

        sql = """
            SELECT entidad_id, hecho_id, tipo, descripcion,
                   estado_economico, estado_epistemologico,
                   ocurrido_inicio, ocurrido_fin, precision_temporal,
                   conocido_en, registrado_en
            FROM dominio_hecho
            WHERE """ + " AND ".join(condiciones) + " ORDER BY registrado_en, hecho_id"

        return self._ejecutar_select(sql, tuple(parametros))

    def listar_eventos(
        self,
        entidad_id: str,
        desde_indice: Optional[int] = None,
        hasta_indice: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        condiciones = ["entidad_id = %s"]
        parametros: list[Any] = [entidad_id]

        if desde_indice is not None:
            condiciones.append("indice >= %s")
            parametros.append(desde_indice)

        if hasta_indice is not None:
            condiciones.append("indice <= %s")
            parametros.append(hasta_indice)

        sql = """
            SELECT entidad_id, evento_id, indice, tipo, objeto_tipo,
                   objeto_id, actor_id, timestamp, estado_anterior,
                   estado_posterior, motivo, referencias, payload,
                   huella, hash_previo, hash
            FROM dominio_evento
            WHERE """ + " AND ".join(condiciones) + " ORDER BY indice"

        return self._ejecutar_select(sql, tuple(parametros))

    def reconstruir_descriptor(self, entidad_id: str) -> dict[str, Any]:
        hechos = self.listar_hechos(entidad_id)
        eventos = self.listar_eventos(entidad_id)
        representaciones = self._ejecutar_select(
            """
            SELECT entidad_id, representacion_id, interpretacion_id,
                   decision_id, marco, fecha_contable, estado, metadatos
            FROM dominio_representacion
            WHERE entidad_id = %s
            ORDER BY fecha_contable, representacion_id
            """,
            (entidad_id,),
        )
        return {
            "entidad_id": entidad_id,
            "hechos": hechos,
            "eventos": eventos,
            "representaciones": representaciones,
        }
