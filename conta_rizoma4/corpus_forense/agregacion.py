# -*- coding: utf-8 -*-
"""Agregación del corpus forense: totales, distribución, patrones."""
from __future__ import annotations

import os
from collections import Counter, defaultdict
from typing import Optional

import psycopg
from psycopg.rows import dict_row


PG_URL = os.environ.get(
    "CONTA_PG_URL",
    "postgresql://rizoma:rizoma_dev@localhost:5433/conta_rizoma4",
)


def agregar_corpus(
    universo: Optional[str] = None,
    pg_url: Optional[str] = None,
) -> dict:
    """Agrega el corpus: totales, distribución por universo, sector, año."""
    url = pg_url or PG_URL
    where = ""
    params = []
    if universo:
        where = "WHERE e.universo = %s"
        params.append(universo)

    with psycopg.connect(url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            # Totales
            cur.execute(
                f"""SELECT
                    COUNT(*) AS n_expedientes,
                    COUNT(DISTINCT e.sujeto_id) AS n_sujetos,
                    COALESCE(SUM(d.principal_debido_centimos), 0) AS principal,
                    COALESCE(SUM(d.interes_renunciado_centimos), 0) AS interes_renunciado,
                    COALESCE(SUM(d.interes_compuesto_centimos), 0) AS interes_compuesto,
                    COALESCE(SUM(d.dano_total_centimos), 0) AS dano_total
                FROM expedientes e
                LEFT JOIN danos d ON d.expediente_id = e.expediente_id
                {where}""",
                params,
            )
            totales = cur.fetchone()

            # Distribución por universo
            cur.execute(
                f"""SELECT universo, COUNT(*) AS n
                FROM expedientes e
                {where}
                GROUP BY universo
                ORDER BY n DESC""",
                params,
            )
            por_universo = cur.fetchall()

            # Distribución por sector
            cur.execute(
                f"""SELECT s.sector, COUNT(*) AS n,
                    COALESCE(SUM(d.dano_total_centimos), 0) AS dano
                FROM expedientes e
                JOIN sujetos s ON s.sujeto_id = e.sujeto_id
                LEFT JOIN danos d ON d.expediente_id = e.expediente_id
                {where}
                GROUP BY s.sector
                ORDER BY dano DESC""",
                params,
            )
            por_sector = cur.fetchall()

            # Distribución por estado del concurso
            cur.execute(
                f"""SELECT estado_concurso, COUNT(*) AS n
                FROM expedientes e
                {where}
                GROUP BY estado_concurso
                ORDER BY n DESC""",
                params,
            )
            por_estado = cur.fetchall()

    return {
        "totales": totales,
        "por_universo": por_universo,
        "por_sector": por_sector,
        "por_estado_concurso": por_estado,
    }


def detectar_patrones(pg_url: Optional[str] = None) -> dict:
    """Detecta patrones anómalos en el corpus.

    Patrones:
      1. Tasa de U1 por sector: si un sector tiene una tasa de U1
         anormalmente alta, puede indicar coacción estructural.
      2. Tasa de sección sexta: si es alta, puede indicar que LO PÚBLICO
         forzó la calificación culpable.
      3. Tasa de no diligencia: si es alta, puede indicar que LO PÚBLICO
         forzó el incidente concursal.
      4. Concentración de daño: si pocas víctimas concentran la mayor
         parte del daño, puede indicar un patrón de selección.
    """
    url = pg_url or PG_URL
    with psycopg.connect(url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            # Tasa de U1 por sector
            cur.execute(
                """SELECT s.sector,
                    COUNT(*) AS total,
                    SUM(CASE WHEN e.universo = 'U1' THEN 1 ELSE 0 END) AS u1,
                    ROUND(100.0 * SUM(CASE WHEN e.universo = 'U1' THEN 1 ELSE 0 END) / COUNT(*), 2) AS tasa_u1
                FROM expedientes e
                JOIN sujetos s ON s.sujeto_id = e.sujeto_id
                GROUP BY s.sector
                ORDER BY tasa_u1 DESC"""
            )
            tasa_u1_por_sector = cur.fetchall()

            # Tasa de sección sexta
            cur.execute(
                """SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN seccion_sexta THEN 1 ELSE 0 END) AS con_seccion,
                    ROUND(100.0 * SUM(CASE WHEN seccion_sexta THEN 1 ELSE 0 END) / COUNT(*), 2) AS tasa
                FROM expedientes
                WHERE estado_concurso != 'ninguno'"""
            )
            tasa_seccion = cur.fetchone()

            # Tasa de no diligencia
            cur.execute(
                """SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN incidente_concursal_por_no_diligencia THEN 1 ELSE 0 END) AS no_diligente,
                    ROUND(100.0 * SUM(CASE WHEN incidente_concursal_por_no_diligencia THEN 1 ELSE 0 END) / COUNT(*), 2) AS tasa
                FROM expedientes"""
            )
            tasa_no_diligencia = cur.fetchone()

            # Concentración de daño (top 10)
            cur.execute(
                """SELECT e.expediente_id, s.nombre, d.dano_total_centimos
                FROM expedientes e
                JOIN sujetos s ON s.sujeto_id = e.sujeto_id
                LEFT JOIN danos d ON d.expediente_id = e.expediente_id
                WHERE d.dano_total_centimos IS NOT NULL
                ORDER BY d.dano_total_centimos DESC
                LIMIT 10"""
            )
            top_dano = cur.fetchall()

    return {
        "tasa_u1_por_sector": tasa_u1_por_sector,
        "tasa_seccion_sexta": tasa_seccion,
        "tasa_no_diligencia": tasa_no_diligencia,
        "top_dano": top_dano,
        "alertas": _generar_alertas(
            tasa_u1_por_sector, tasa_seccion, tasa_no_diligencia,
        ),
    }


def _generar_alertas(
    tasa_u1_por_sector: list[dict],
    tasa_seccion: dict,
    tasa_no_diligencia: dict,
) -> list[str]:
    """Genera alertas si hay patrones anómalos."""
    alertas = []

    # 1. Sector con tasa de U1 > 80%
    for s in tasa_u1_por_sector:
        if s["tasa_u1"] and s["tasa_u1"] > 80.0 and s["total"] >= 2:
            alertas.append(
                f"Sector '{s['sector']}' con tasa de U1 del {s['tasa_u1']}% "
                f"({s['u1']}/{s['total']}). Posible coacción estructural."
            )

    # 2. Tasa de sección sexta > 30%
    if tasa_seccion["tasa"] and tasa_seccion["tasa"] > 30.0:
        alertas.append(
            f"Tasa de sección sexta del {tasa_seccion['tasa']}% "
            f"({tasa_seccion['con_seccion']}/{tasa_seccion['total']}). "
            f"Posible forzamiento de calificación culpable."
        )

    # 3. Tasa de no diligencia > 20%
    if tasa_no_diligencia["tasa"] and tasa_no_diligencia["tasa"] > 20.0:
        alertas.append(
            f"Tasa de no diligencia del {tasa_no_diligencia['tasa']}% "
            f"({tasa_no_diligencia['no_diligente']}/{tasa_no_diligencia['total']}). "
            f"Posible forzamiento de incidente concursal."
        )

    return alertas
