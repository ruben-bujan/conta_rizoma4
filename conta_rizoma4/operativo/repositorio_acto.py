# -*- coding: utf-8 -*-
"""RepositorioActoEconomico: lectura/escritura/verificación de la cadena."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

import psycopg
from psycopg.rows import dict_row

from .asiento import GENESIS, calcular_hash, calcular_huella
from .acto_economico import (
    ActoEconomico,
    crear_acto_economico,
    guardar_acto_economico,
)


PG_URL = os.environ.get(
    "CONTA_PG_URL",
    "postgresql://rizoma:rizoma_dev@localhost:5433/conta_rizoma4",
)


_COLUMNAS = (
    "indice, fecha, cuenta_pgc, importe_centimos, moneda, concepto, "
    "actividad_nivel, actividad_id, interlocutor_tipo, interlocutor_nif, "
    "documento_tipo, documento_ref, parrafo_pgc_id, "
    "justificacion_indice, cuenta_contrapartida, "
    "creado_por, validado_por, aprobado_por, "
    "huella_contenido, hash_previo, hash, metadatos"
)


@dataclass
class ReporteCadena:
    desde: int
    hasta: int
    total: int
    cadena_valida: bool
    roturas: list[dict]


class RepositorioActoEconomico:
    def __init__(self, pg_url: Optional[str] = None):
        self._url = pg_url or PG_URL

    def _conn(self):
        return psycopg.connect(self._url, row_factory=dict_row)

    def obtener(self, indice: int) -> Optional[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {_COLUMNAS} FROM acto_economico WHERE indice = %s",
                    (indice,),
                )
                return cur.fetchone()

    def listar(
        self,
        *,
        indice_desde: Optional[int] = None,
        indice_hasta: Optional[int] = None,
        cuenta: Optional[str] = None,
        limite: int = 100,
    ) -> list[dict]:
        where, params = [], []
        if indice_desde is not None:
            where.append("indice >= %s"); params.append(indice_desde)
        if indice_hasta is not None:
            where.append("indice <= %s"); params.append(indice_hasta)
        if cuenta is not None:
            where.append("cuenta_pgc = %s"); params.append(cuenta)
        sql = f"SELECT {_COLUMNAS} FROM acto_economico"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY indice ASC LIMIT %s"
        params.append(limite)
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchall()

    def por_cuenta(self, cuenta: str, limite: int = 100) -> list[dict]:
        return self.listar(cuenta=cuenta, limite=limite)

    def por_fecha(self, desde: date, hasta: date, limite: int = 1000) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {_COLUMNAS} FROM acto_economico "
                    "WHERE fecha >= %s AND fecha <= %s "
                    "ORDER BY indice ASC LIMIT %s",
                    (desde, hasta, limite),
                )
                return cur.fetchall()

    def actos_que_resuelven(self, justificacion_indice: int) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {_COLUMNAS} FROM acto_economico "
                    "WHERE justificacion_indice = %s ORDER BY indice ASC",
                    (justificacion_indice,),
                )
                return cur.fetchall()

    def contar(self) -> int:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS n FROM acto_economico")
                return cur.fetchone()["n"]

    def ultimo_indice(self) -> int:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT MAX(indice) AS m FROM acto_economico")
                m = cur.fetchone()["m"]
        return -1 if m is None else int(m)

    def siguiente_indice(self) -> int:
        return self.ultimo_indice() + 1

    def crear_siguiente(
        self,
        *,
        fecha: date,
        cuenta_pgc: str,
        importe_centimos: int,
        concepto: str,
        creado_por: str,
        **kwargs: Any,
    ) -> ActoEconomico:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT indice, hash FROM acto_economico "
                    "ORDER BY indice DESC LIMIT 1"
                )
                row = cur.fetchone()
        if row:
            hash_previo = row["hash"]
            indice = row["indice"] + 1
        else:
            hash_previo = GENESIS
            indice = 0
        acto = crear_acto_economico(
            indice=indice, fecha=fecha, cuenta_pgc=cuenta_pgc,
            importe_centimos=importe_centimos, concepto=concepto,
            creado_por=creado_por, hash_previo=hash_previo, **kwargs,
        )
        guardar_acto_economico(acto, pg_url=self._url)
        return acto

    def verificar_cadena(
        self,
        desde: Optional[int] = None,
        hasta: Optional[int] = None,
    ) -> ReporteCadena:
        actos = self.listar(indice_desde=desde, indice_hasta=hasta, limite=100_000)
        if not actos:
            return ReporteCadena(
                desde=desde if desde is not None else 0,
                hasta=hasta if hasta is not None else 0,
                total=0, cadena_valida=True, roturas=[],
            )
        roturas: list[dict] = []
        for i, acto in enumerate(actos):
            contenido = _reconstruir_contenido(acto)
            huella_calc = calcular_huella(contenido)
            if huella_calc != acto["huella_contenido"]:
                roturas.append({
                    "indice": acto["indice"], "tipo": "huella_no_coincide",
                    "esperado": huella_calc, "guardado": acto["huella_contenido"],
                })
            hash_calc = calcular_hash(
                acto["huella_contenido"], acto["hash_previo"], acto["indice"],
            )
            if hash_calc != acto["hash"]:
                roturas.append({
                    "indice": acto["indice"], "tipo": "hash_no_coincide",
                    "esperado": hash_calc, "guardado": acto["hash"],
                })
            if i == 0:
                if desde is None or desde == 0:
                    if acto["hash_previo"] != GENESIS:
                        roturas.append({
                            "indice": acto["indice"],
                            "tipo": "primer_acto_no_genesis",
                            "esperado": GENESIS,
                            "guardado": acto["hash_previo"],
                        })
            else:
                if acto["hash_previo"] != actos[i - 1]["hash"]:
                    roturas.append({
                        "indice": acto["indice"], "tipo": "rotura_cadena",
                        "esperado": actos[i - 1]["hash"],
                        "guardado": acto["hash_previo"],
                    })
        return ReporteCadena(
            desde=actos[0]["indice"], hasta=actos[-1]["indice"],
            total=len(actos), cadena_valida=len(roturas) == 0, roturas=roturas,
        )


def _reconstruir_contenido(row: dict) -> dict:
    fecha = row["fecha"]
    fecha_str = fecha.isoformat() if hasattr(fecha, "isoformat") else str(fecha)
    metadatos = row["metadatos"]
    if isinstance(metadatos, str):
        metadatos = json.loads(metadatos)
    if metadatos is None:
        metadatos = {}

    contenido = {
        "fecha": fecha_str,
        "cuenta_pgc": row["cuenta_pgc"],
        "importe_centimos": row["importe_centimos"],
        "moneda": row["moneda"],
        "concepto": row["concepto"],
        "actividad_nivel": row["actividad_nivel"],
        "actividad_id": row["actividad_id"],
        "interlocutor_tipo": row["interlocutor_tipo"],
        "interlocutor_nif": row["interlocutor_nif"],
        "documento_tipo": row["documento_tipo"],
        "documento_ref": row["documento_ref"],
        "parrafo_pgc_id": row["parrafo_pgc_id"],
        "creado_por": row["creado_por"],
        "validado_por": row["validado_por"],
        "aprobado_por": row["aprobado_por"],
        "metadatos": metadatos,
    }
    if row.get("justificacion_indice") is not None:
        contenido["justificacion_indice"] = row["justificacion_indice"]
    if row.get("cuenta_contrapartida") is not None:
        contenido["cuenta_contrapartida"] = row["cuenta_contrapartida"]
    return contenido
