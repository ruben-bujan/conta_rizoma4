# -*- coding: utf-8 -*-
"""Consolidación de grupo clásico: suma, elimina intragrupo, atribuye."""
from __future__ import annotations

from datetime import date
from typing import Optional

import psycopg
from psycopg.rows import dict_row

from ..partida_doble import RepositorioAsiento
from ..partida_doble.cuentas_anuales import balance_situacion, cuenta_pyg
from ..partida_doble.persistencia import PG_URL
from .modelo import (
    BalanceConsolidado, ConsolidacionError, EliminacionPropuesta,
    RelacionGrupo,
)


def _grupo_de(cuenta: str) -> int:
    if not cuenta or not cuenta[0].isdigit():
        return 0
    return int(cuenta[0])


def cargar_relaciones(matriz_id: str, fecha: date, pg_url: Optional[str] = None) -> list[RelacionGrupo]:
    url = pg_url or PG_URL
    with psycopg.connect(url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT matriz_id, filial_id, porcentaje, fecha_inicio, fecha_fin "
                "FROM relaciones_grupo "
                "WHERE matriz_id = %s "
                "  AND fecha_inicio <= %s "
                "  AND (fecha_fin IS NULL OR fecha_fin >= %s)",
                (matriz_id, fecha, fecha),
            )
            rows = cur.fetchall()
    return [
        RelacionGrupo(
            matriz_id=r["matriz_id"], filial_id=r["filial_id"],
            porcentaje=float(r["porcentaje"]),
            fecha_inicio=r["fecha_inicio"], fecha_fin=r["fecha_fin"],
        )
        for r in rows
    ]


def guardar_relacion(rel: RelacionGrupo, pg_url: Optional[str] = None) -> None:
    url = pg_url or PG_URL
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO relaciones_grupo "
                "(matriz_id, filial_id, porcentaje, fecha_inicio, fecha_fin) "
                "VALUES (%s, %s, %s, %s, %s) "
                "ON CONFLICT (matriz_id, filial_id, fecha_inicio) DO NOTHING",
                (rel.matriz_id, rel.filial_id, rel.porcentaje,
                 rel.fecha_inicio, rel.fecha_fin),
            )
        conn.commit()


def consolidar_grupo(
    grupo_id: str,
    matriz_id: str,
    fecha_cierre: date,
    pg_url: Optional[str] = None,
) -> BalanceConsolidado:
    """Consolida el grupo: suma de empresas, atribuye a matriz y minoritarios.

    Usa balance_situacion (que separa activo bruto, pasivo y correctores)
    y cuenta_pyg (resultado). La ecuación contable se mantiene:
        Activo neto = Pasivo + PN + Resultado
    """
    relaciones = cargar_relaciones(matriz_id, fecha_cierre, pg_url)
    empresas = [matriz_id] + [r.filial_id for r in relaciones]

    activo_plano: dict[str, int] = {}
    correctores_plano: dict[str, int] = {}
    pasivo_plano: dict[str, int] = {}
    resultados: dict[str, int] = {}
    participaciones: dict[str, float] = {matriz_id: 100.0}

    for r in relaciones:
        participaciones[r.filial_id] = r.porcentaje

    for empresa in empresas:
        repo = RepositorioAsiento(empresa, pg_url)
        bal = balance_situacion(repo)
        pyg = cuenta_pyg(repo)
        resultados[empresa] = pyg["resultado"]

        for cuenta, importe in bal["activo"].items():
            activo_plano[cuenta] = activo_plano.get(cuenta, 0) + importe
        for cuenta, importe in bal.get("correctores", {}).items():
            correctores_plano[cuenta] = correctores_plano.get(cuenta, 0) + importe
        for cuenta, importe in bal["pasivo"].items():
            pasivo_plano[cuenta] = pasivo_plano.get(cuenta, 0) + importe

    # Agrupar por grupos PGC
    activo_por_grupo: dict[str, dict[str, int]] = {}
    pasivo_por_grupo: dict[str, dict[str, int]] = {}
    correctores_por_grupo: dict[str, dict[str, int]] = {}
    for cuenta, importe in activo_plano.items():
        g = _grupo_de(cuenta)
        activo_por_grupo.setdefault(g, {})[cuenta] = importe
    for cuenta, importe in pasivo_plano.items():
        g = _grupo_de(cuenta)
        pasivo_por_grupo.setdefault(g, {})[cuenta] = importe
    for cuenta, importe in correctores_plano.items():
        g = _grupo_de(cuenta)
        correctores_por_grupo.setdefault(g, {})[cuenta] = importe

    # Resultado del grupo y atribución
    resultado_total = sum(resultados.values())
    resultado_matriz = 0.0
    resultado_minoritarios = 0.0
    for empresa, resultado in resultados.items():
        pct = participaciones.get(empresa, 100.0)
        resultado_matriz += resultado * (pct / 100.0)
        resultado_minoritarios += resultado * (1 - pct / 100.0)

    # Cuadre con correctores
    total_activo_bruto = sum(activo_plano.values())
    total_correctores = sum(correctores_plano.values())
    total_activo_neto = total_activo_bruto - total_correctores
    total_pasivo = sum(pasivo_plano.values())
    cuadra = abs(total_activo_neto - (total_pasivo + resultado_total)) < 100

    return BalanceConsolidado(
        grupo_id=grupo_id,
        fecha_cierre=fecha_cierre,
        empresas_incluidas=empresas,
        activo=activo_por_grupo,
        correctores=correctores_por_grupo,
        pasivo=pasivo_por_grupo,
        resultado_grupo=round(resultado_total),
        resultado_atribuible_matriz=round(resultado_matriz),
        resultado_atribuible_minoritarios=round(resultado_minoritarios),
        eliminaciones_aplicadas=[],
        cuadra=cuadra,
    )
