# -*- coding: utf-8 -*-
"""Repositorios del corpus forense."""
from __future__ import annotations

import json
import os
from datetime import date
from typing import Optional

import psycopg
from psycopg.rows import dict_row

from ..operativo.asiento import GENESIS, calcular_hash, calcular_huella
from .modelo import (
    Dano, Expediente, Flujo, Sujeto, clasificar_expediente,
)


PG_URL = os.environ.get(
    "CONTA_PG_URL",
    "postgresql://rizoma:rizoma_dev@localhost:5433/conta_rizoma4",
)


class RepositorioSujeto:
    def __init__(self, pg_url: Optional[str] = None):
        self._url = pg_url or PG_URL

    def _conn(self):
        return psycopg.connect(self._url, row_factory=dict_row)

    def crear(self, s: Sujeto) -> Sujeto:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO sujetos
                    (sujeto_id, tipo, nombre, nif, sector, anonimizado, metadatos)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (sujeto_id) DO NOTHING""",
                    (s.sujeto_id, s.tipo, s.nombre, s.nif, s.sector,
                     s.anonimizado, json.dumps(s.metadatos)),
                )
            conn.commit()
        return s

    def obtener(self, sujeto_id: str) -> Optional[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM sujetos WHERE sujeto_id = %s",
                            (sujeto_id,))
                return cur.fetchone()

    def listar(self, tipo: Optional[str] = None) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                if tipo:
                    cur.execute(
                        "SELECT * FROM sujetos WHERE tipo = %s ORDER BY sujeto_id",
                        (tipo,),
                    )
                else:
                    cur.execute("SELECT * FROM sujetos ORDER BY sujeto_id")
                return cur.fetchall()


class RepositorioExpediente:
    def __init__(self, pg_url: Optional[str] = None):
        self._url = pg_url or PG_URL

    def _conn(self):
        return psycopg.connect(self._url, row_factory=dict_row)

    def crear(self, e: Expediente) -> Expediente:
        # Clasificar
        universo, reparacion = clasificar_expediente(e)
        e.universo = universo
        e.tipo_reparacion = reparacion

        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO expedientes
                    (expediente_id, sujeto_id, contrato_publico_ref,
                     tipo_contrato, fecha_inicio, fecha_fin,
                     via_u1, es_punta_de_lanza,
                     estado_concurso, fecha_concurso, fecha_conclusion,
                     seccion_sexta, calificacion,
                     incidente_concursal_por_no_diligencia,
                     buena_fe_acreditada, medio_prueba_buena_fe,
                     nivel_vida_antes_centimos, nivel_vida_despues_centimos,
                     porcentaje_menoscabo, quiebra_modo_vida,
                     universo, tipo_reparacion, metadatos)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (expediente_id) DO NOTHING""",
                    (e.expediente_id, e.sujeto_id, e.contrato_publico_ref,
                     e.tipo_contrato, e.fecha_inicio, e.fecha_fin,
                     e.via_u1, e.es_punta_de_lanza,
                     e.estado_concurso, e.fecha_concurso, e.fecha_conclusion,
                     e.seccion_sexta, e.calificacion,
                     e.incidente_concursal_por_no_diligencia,
                     e.buena_fe_acreditada, e.medio_prueba_buena_fe,
                     e.nivel_vida_antes_centimos, e.nivel_vida_despues_centimos,
                     e.porcentaje_menoscabo, e.quiebra_modo_vida,
                     e.universo, e.tipo_reparacion,
                     json.dumps(e.metadatos)),
                )
            conn.commit()
        return e

    def obtener(self, expediente_id: str) -> Optional[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM expedientes WHERE expediente_id = %s",
                    (expediente_id,),
                )
                return cur.fetchone()

    def listar(
        self, universo: Optional[str] = None, sujeto_id: Optional[str] = None,
    ) -> list[dict]:
        where, params = [], []
        if universo:
            where.append("universo = %s"); params.append(universo)
        if sujeto_id:
            where.append("sujeto_id = %s"); params.append(sujeto_id)
        sql = "SELECT * FROM expedientes"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY expediente_id"
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchall()


class RepositorioFlujo:
    def __init__(self, pg_url: Optional[str] = None):
        self._url = pg_url or PG_URL

    def _conn(self):
        return psycopg.connect(self._url, row_factory=dict_row)

    def crear(self, f: Flujo) -> Flujo:
        # Hash chain
        contenido = {
            "expediente_id": f.expediente_id,
            "fecha": f.fecha.isoformat(),
            "concepto": f.concepto,
            "importe_centimos": f.importe_centimos,
            "categoria": f.categoria,
            "documento_ref": f.documento_ref,
        }
        huella = calcular_huella(contenido)
        hash_ = calcular_hash(huella, f.hash_previo or GENESIS, f.id)
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO flujos
                    (expediente_id, fecha, concepto, importe_centimos,
                     categoria, documento_ref, hash_previo, hash)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id""",
                    (f.expediente_id, f.fecha, f.concepto, f.importe_centimos,
                     f.categoria, f.documento_ref, f.hash_previo, hash_),
                )
                new_id = cur.fetchone()["id"]
            conn.commit()
        return Flujo(
            id=new_id, expediente_id=f.expediente_id, fecha=f.fecha,
            concepto=f.concepto, importe_centimos=f.importe_centimos,
            categoria=f.categoria, documento_ref=f.documento_ref,
            hash_previo=f.hash_previo, hash=hash_,
        )

    def listar(self, expediente_id: str) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM flujos WHERE expediente_id = %s ORDER BY fecha, id",
                    (expediente_id,),
                )
                return cur.fetchall()


class RepositorioDano:
    def __init__(self, pg_url: Optional[str] = None):
        self._url = pg_url or PG_URL

    def _conn(self):
        return psycopg.connect(self._url, row_factory=dict_row)

    def crear(self, d: Dano) -> Dano:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO danos
                    (expediente_id, principal_debido_centimos,
                     interes_renunciado_centimos, interes_compuesto_centimos,
                     dano_moral_centimos, consecuencias_indirectas_centimos,
                     dano_total_centimos, fecha_corte)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (expediente_id) DO UPDATE SET
                        principal_debido_centimos = EXCLUDED.principal_debido_centimos,
                        interes_renunciado_centimos = EXCLUDED.interes_renunciado_centimos,
                        interes_compuesto_centimos = EXCLUDED.interes_compuesto_centimos,
                        dano_total_centimos = EXCLUDED.dano_total_centimos,
                        calculado_en = NOW()""",
                    (d.expediente_id, d.principal_debido_centimos,
                     d.interes_renunciado_centimos, d.interes_compuesto_centimos,
                     d.dano_moral_centimos, d.consecuencias_indirectas_centimos,
                     d.dano_total_centimos, d.fecha_corte),
                )
            conn.commit()
        return d

    def obtener(self, expediente_id: str) -> Optional[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM danos WHERE expediente_id = %s",
                    (expediente_id,),
                )
                return cur.fetchone()
