"""Lectura paginada y sin escrituras del lote fuente de INCIVSA."""
from __future__ import annotations

from typing import Any

from .postgresql_lectura import RepositorioPostgresLectura


class RepositorioINCIVSALectura:
    def __init__(self, pg_url: str) -> None:
        self._repo = RepositorioPostgresLectura(pg_url)

    def listar_lotes(self, empresa_id: str, limite: int = 50) -> list[dict[str, Any]]:
        if not empresa_id or not 1 <= limite <= 200:
            raise ValueError("empresa_id y límite entre 1 y 200 son obligatorios")
        return self._repo._ejecutar_select(
            """
            SELECT l.lote_id, l.empresa_id, l.fuente, l.sha256_fuente,
                   l.version_parser, l.total_grupos, l.total_filas_origen,
                   l.grupos_propuestos, l.grupos_no_determinados, l.creado_en,
                   COALESCE(g.grupos_consultables, 0) AS grupos_consultables
            FROM incivsa_lote_importacion AS l
            LEFT JOIN (
                SELECT lote_id, COUNT(*) AS grupos_consultables
                FROM incivsa_grupo_origen GROUP BY lote_id
            ) AS g ON g.lote_id = l.lote_id
            WHERE l.empresa_id = %s
            ORDER BY l.creado_en DESC, l.lote_id
            LIMIT %s
            """,
            (empresa_id, limite),
        )

    def obtener_lote(self, empresa_id: str, lote_id: str) -> dict[str, Any] | None:
        if not empresa_id or not lote_id:
            raise ValueError("empresa_id y lote_id son obligatorios")
        filas = self._repo._ejecutar_select(
            """
            SELECT l.lote_id, l.empresa_id, l.fuente, l.sha256_fuente,
                   l.version_parser, l.total_grupos, l.total_filas_origen,
                   l.grupos_propuestos, l.grupos_no_determinados, l.creado_en,
                   COALESCE(g.estados, '{}'::jsonb) AS estados
            FROM incivsa_lote_importacion AS l
            LEFT JOIN (
                SELECT lote_id, jsonb_object_agg(estado_migracion, cantidad) AS estados
                FROM (
                    SELECT lote_id, estado_migracion, COUNT(*) AS cantidad
                    FROM incivsa_grupo_origen GROUP BY lote_id, estado_migracion
                ) AS conteo GROUP BY lote_id
            ) AS g ON g.lote_id = l.lote_id
            WHERE l.empresa_id = %s AND l.lote_id = %s
            """,
            (empresa_id, lote_id),
        )
        return filas[0] if filas else None

    def listar_grupos(
        self, empresa_id: str, lote_id: str, *, estado: str | None = None,
        limite: int = 50, desplazamiento: int = 0,
    ) -> list[dict[str, Any]]:
        if not empresa_id or not lote_id:
            raise ValueError("empresa_id y lote_id son obligatorios")
        if not 1 <= limite <= 200 or desplazamiento < 0:
            raise ValueError("paginación no válida")
        condiciones = ["empresa_id = %s", "lote_id = %s"]
        parametros: list[Any] = [empresa_id, lote_id]
        if estado:
            condiciones.append("estado_migracion = %s")
            parametros.append(estado)
        parametros.extend((limite, desplazamiento))
        return self._repo._ejecutar_select(
            f"""
            SELECT lote_id, empresa_id, clave_origen_sha256, codigo_origen,
                   fecha_origen, estado_migracion, filas_origen,
                   lineas_propuestas, error_origen, asiento_indice
            FROM incivsa_grupo_origen
            WHERE {' AND '.join(condiciones)}
            ORDER BY codigo_origen, fecha_origen, clave_origen_sha256
            LIMIT %s OFFSET %s
            """,
            tuple(parametros),
        )
