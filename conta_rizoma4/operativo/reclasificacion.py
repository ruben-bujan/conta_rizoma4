# -*- coding: utf-8 -*-
"""Reclasificación de una JustificacionInterna cuando llega la factura.

Flujo típico:
  1. Obra ejecutada (devengo):   JustificacionInterna → cuenta 4308
  2. Llega factura (reclasif.):  ActoEconomico → 430 (contrapartida 4308)

El ActoEconomico resultante lleva:
  - justificacion_indice = indice de la JustificacionInterna
  - cuenta_contrapartida = cuenta de la JustificacionInterna (4308)
  - cuenta_pgc           = cuenta destino (430)

Así, la cadena de actos queda enlazada con la justificación, y
verificar_cadena() detecta si alguien manipula el enlace.
"""
from __future__ import annotations

import os
from datetime import date
from typing import Optional

import psycopg
from psycopg.rows import dict_row

from .acto_economico import ActoEconomico
from .justificacion_interna import JustificacionInterna
from .repositorio_acto import RepositorioActoEconomico


PG_URL = os.environ.get(
    "CONTA_PG_URL",
    "postgresql://rizoma:rizoma_dev@localhost:5433/conta_rizoma4",
)

CUENTA_DESTINO_DEFAULT = "430"   # Clientes
CUENTA_ORIGEN_DEFAULT = "4308"   # Clientes, obra ejecutada pendiente


class ReclasificacionError(Exception):
    """Error en el proceso de reclasificación."""


def reclasificar_justificacion(
    justificacion: JustificacionInterna,
    *,
    creado_por: str,
    cuenta_destino: str = CUENTA_DESTINO_DEFAULT,
    fecha: Optional[date] = None,
    concepto: Optional[str] = None,
    repo: Optional[RepositorioActoEconomico] = None,
    metadatos: Optional[dict] = None,
) -> ActoEconomico:
    """Crea el acto que reclasifica el devengo.

    Args:
        justificacion: la JustificacionInterna a resolver.
        creado_por: quién firma la reclasificación (cadena de mando).
        cuenta_destino: cuenta que recibe el importe (default: 430 Clientes).
        fecha: fecha de la factura (default: hoy).
        concepto: descripción libre (default: "Facturación de X").
        repo: repositorio de actos (default: uno nuevo).
        metadatos: dict libre para marcar el acto (default: None → {}).

    Returns:
        El ActoEconomico creado.

    Raises:
        ReclasificacionError: si la justificación ya está reclasificada,
            o si cuenta_destino == justificacion.cuenta_pgc, o si el
            importe es 0.
    """
    if not creado_por:
        raise ReclasificacionError("creado_por es obligatorio")

    if cuenta_destino == justificacion.cuenta_pgc:
        raise ReclasificacionError(
            f"cuenta_destino ({cuenta_destino}) == cuenta_origen "
            f"({justificacion.cuenta_pgc}): sería un no-op"
        )

    if justificacion.importe_centimos == 0:
        raise ReclasificacionError(
            "importe_centimos == 0: no hay nada que reclasificar"
        )

    repo = repo or RepositorioActoEconomico()

    actos_previos = repo.actos_que_resuelven(justificacion.indice)
    if actos_previos:
        idx = [a["indice"] for a in actos_previos]
        raise ReclasificacionError(
            f"JustificacionInterna {justificacion.indice} ya reclasificada "
            f"por acto(s) {idx}"
        )

    acto = repo.crear_siguiente(
        fecha=fecha or date.today(),
        cuenta_pgc=cuenta_destino,
        importe_centimos=justificacion.importe_centimos,
        concepto=concepto or f"Facturación de {justificacion.concepto}",
        creado_por=creado_por,
        justificacion_indice=justificacion.indice,
        cuenta_contrapartida=justificacion.cuenta_pgc,
        metadatos=metadatos,
    )
    return acto


def justificaciones_pendientes(pg_url: Optional[str] = None) -> list[dict]:
    """Justificaciones internas sin acto que las resuelva."""
    url = pg_url or PG_URL
    with psycopg.connect(url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT j.* FROM justificacion_interna j
                LEFT JOIN acto_economico a
                    ON a.justificacion_indice = j.indice
                WHERE a.indice IS NULL
                ORDER BY j.indice ASC
                """
            )
            return cur.fetchall()


def justificaciones_reclasificadas(pg_url: Optional[str] = None) -> list[dict]:
    """Justificaciones internas ya resueltas, con datos del acto."""
    url = pg_url or PG_URL
    with psycopg.connect(url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    j.indice          AS justificacion_indice,
                    j.concepto        AS justificacion_concepto,
                    j.importe_centimos,
                    j.fecha           AS fecha_justificacion,
                    a.indice          AS acto_indice,
                    a.fecha           AS fecha_factura,
                    a.cuenta_pgc      AS cuenta_destino,
                    a.cuenta_contrapartida
                FROM justificacion_interna j
                JOIN acto_economico a
                    ON a.justificacion_indice = j.indice
                ORDER BY j.indice ASC
                """
            )
            return cur.fetchall()
