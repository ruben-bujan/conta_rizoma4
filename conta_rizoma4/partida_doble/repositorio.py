# -*- coding: utf-8 -*-
"""RepositorioAsiento: lectura + verificación de la cadena."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import psycopg
from psycopg.rows import dict_row

from ..operativo.asiento import GENESIS, calcular_hash, calcular_huella


PG_URL = os.environ.get(
    "CONTA_PG_URL",
    "postgresql://rizoma:rizoma_dev@localhost:5433/conta_rizoma4",
)


@dataclass
class ReporteCadenaAsientos:
    desde: int
    hasta: int
    total: int
    cadena_valida: bool
    roturas: list[dict]


class RepositorioAsiento:
    def __init__(self, pg_url: Optional[str] = None):
        self._url = pg_url or PG_URL

    def _conn(self):
        return psycopg.connect(self._url, row_factory=dict_row)

    def obtener(self, indice: int) -> Optional[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT indice, fecha, concepto, hash_previo, hash, metadatos "
                    "FROM asiento_contable WHERE indice = %s", (indice,),
                )
                cab = cur.fetchone()
                if cab is None:
                    return None
                cur.execute(
                    "SELECT cuenta_pgc, debe_centimos, haber_centimos, "
                    "parrafo_pgc_id, concepto_linea "
                    "FROM linea_asiento WHERE asiento_indice = %s ORDER BY id",
                    (indice,),
                )
                cab["lineas"] = cur.fetchall()
                return cab

    def listar(
        self,
        *,
        indice_desde: Optional[int] = None,
        indice_hasta: Optional[int] = None,
        limite: int = 100,
    ) -> list[dict]:
        where, params = [], []
        if indice_desde is not None:
            where.append("indice >= %s"); params.append(indice_desde)
        if indice_hasta is not None:
            where.append("indice <= %s"); params.append(indice_hasta)
        sql = "SELECT indice, fecha, concepto, hash_previo, hash, metadatos FROM asiento_contable"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY indice ASC LIMIT %s"
        params.append(limite)
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchall()

    def ultimo_indice(self) -> int:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT MAX(indice) AS m FROM asiento_contable")
                m = cur.fetchone()["m"]
        return -1 if m is None else int(m)

    def contar(self) -> int:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS n FROM asiento_contable")
                return cur.fetchone()["n"]

    def _huella_de(self, indice: int) -> str:
        d = self.obtener(indice)
        contenido = {
            "fecha": d["fecha"].isoformat(),
            "concepto": d["concepto"],
            "lineas": [
                {
                    "cuenta_pgc": l["cuenta_pgc"],
                    "debe_centimos": l["debe_centimos"],
                    "haber_centimos": l["haber_centimos"],
                    "parrafo_pgc_id": l["parrafo_pgc_id"],
                    "concepto_linea": l["concepto_linea"],
                }
                for l in d["lineas"]
            ],
            "metadatos": d["metadatos"] or {},
        }
        return calcular_huella(contenido)

    def verificar_cadena(
        self,
        desde: Optional[int] = None,
        hasta: Optional[int] = None,
    ) -> ReporteCadenaAsientos:
        asientos = self.listar(
            indice_desde=desde, indice_hasta=hasta, limite=100_000,
        )
        if not asientos:
            return ReporteCadenaAsientos(
                desde=desde or 0, hasta=hasta or 0,
                total=0, cadena_valida=True, roturas=[],
            )
        roturas: list[dict] = []
        for i, a in enumerate(asientos):
            huella_calc = self._huella_de(a["indice"])
            hash_calc = calcular_hash(huella_calc, a["hash_previo"], a["indice"])
            if hash_calc != a["hash"]:
                roturas.append({
                    "indice": a["indice"], "tipo": "hash_no_coincide",
                    "esperado": hash_calc, "guardado": a["hash"],
                })
            if i == 0:
                if (desde is None or desde == 0) and a["hash_previo"] != GENESIS:
                    roturas.append({
                        "indice": a["indice"],
                        "tipo": "primer_asiento_no_genesis",
                        "esperado": GENESIS,
                        "guardado": a["hash_previo"],
                    })
            else:
                if a["hash_previo"] != asientos[i - 1]["hash"]:
                    roturas.append({
                        "indice": a["indice"], "tipo": "rotura_cadena",
                        "esperado": asientos[i - 1]["hash"],
                        "guardado": a["hash_previo"],
                    })
        return ReporteCadenaAsientos(
            desde=asientos[0]["indice"], hasta=asientos[-1]["indice"],
            total=len(asientos),
            cadena_valida=len(roturas) == 0, roturas=roturas,
        )
