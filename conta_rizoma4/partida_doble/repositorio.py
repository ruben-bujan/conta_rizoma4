# -*- coding: utf-8 -*-
"""RepositorioAsiento multi-tenant con soporte de filtros por fecha (H-09)."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date
from typing import Optional

import psycopg
from psycopg.rows import dict_row

from ..operativo.asiento import GENESIS, calcular_hash, calcular_huella


from ..config.postgresql import PG_URL


@dataclass
class ReporteCadenaAsientos:
    empresa_id: str
    desde: int
    hasta: int
    total: int
    cadena_valida: bool
    roturas: list[dict]


class RepositorioAsiento:
    def __init__(self, empresa_id: str, pg_url: Optional[str] = None):
        if not empresa_id or not empresa_id.strip():
            raise ValueError(
                "empresa_id es obligatorio. "
                "Cada contabilidad es de una empresa distinta."
            )
        self._empresa_id = empresa_id
        self._url = pg_url or PG_URL

    @property
    def empresa_id(self) -> str:
        return self._empresa_id

    def _conn(self):
        return psycopg.connect(self._url, row_factory=dict_row)

    def obtener(self, indice: int) -> Optional[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT indice, caso_id, fecha, concepto, hash_previo, hash, metadatos "
                    "FROM asiento_contable "
                    "WHERE empresa_id = %s AND indice = %s",
                    (self._empresa_id, indice),
                )
                cab = cur.fetchone()
                if cab is None:
                    return None
                cur.execute(
                    "SELECT cuenta_pgc, debe_centimos, haber_centimos, "
                    "parrafo_pgc_id, concepto_linea "
                    "FROM linea_asiento "
                    "WHERE empresa_id = %s AND asiento_indice = %s "
                    "ORDER BY id",
                    (self._empresa_id, indice),
                )
                cab["lineas"] = cur.fetchall()
                return cab

    def listar(
        self,
        *,
        indice_desde: Optional[int] = None,
        indice_hasta: Optional[int] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        limite: int = 100,
        incluir_importaciones_pendientes: bool = False,
    ) -> list[dict]:
        """Lista asientos ordinarios; lotes migrados pendientes requieren inclusión explícita."""
        where = ["empresa_id = %s"]
        params: list = [self._empresa_id]
        if not incluir_importaciones_pendientes:
            where.append("COALESCE(metadatos->>'lote_importacion', '') = ''")
        if indice_desde is not None:
            where.append("indice >= %s"); params.append(indice_desde)
        if indice_hasta is not None:
            where.append("indice <= %s"); params.append(indice_hasta)
        if fecha_desde is not None:
            where.append("fecha >= %s"); params.append(fecha_desde)
        if fecha_hasta is not None:
            where.append("fecha <= %s"); params.append(fecha_hasta)
            
        sql = (
            "SELECT indice, caso_id, fecha, concepto, hash_previo, hash, metadatos "
            "FROM asiento_contable WHERE " + " AND ".join(where) +
            " ORDER BY fecha ASC, indice ASC LIMIT %s"
        )
        params.append(limite)
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchall()

    def ultimo_indice(self) -> int:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT MAX(indice) AS m FROM asiento_contable "
                    "WHERE empresa_id = %s",
                    (self._empresa_id,),
                )
                m = cur.fetchone()["m"]
        return -1 if m is None else int(m)

    def contar(self) -> int:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) AS n FROM asiento_contable "
                    "WHERE empresa_id = %s",
                    (self._empresa_id,),
                )
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

    def listar_por_estado(
        self, estado: str, *, limite: int = 100,
    ) -> list[dict]:
        """Lista asientos filtrados por estado."""
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT indice, caso_id, fecha, concepto, hash_previo, hash, metadatos "
                    "FROM asiento_contable "
                    "WHERE empresa_id = %s AND estado = %s "
                    "ORDER BY fecha ASC, indice ASC LIMIT %s",
                    (self._empresa_id, estado, limite),
                )
                asientos = cur.fetchall()
                for a in asientos:
                    cur.execute(
                        "SELECT cuenta_pgc, debe_centimos, haber_centimos, "
                        "parrafo_pgc_id, concepto_linea "
                        "FROM linea_asiento "
                        "WHERE empresa_id = %s AND asiento_indice = %s "
                        "ORDER BY id",
                        (self._empresa_id, a["indice"]),
                    )
                    a["lineas"] = cur.fetchall()
        return asientos

    def _listar_cadena(
        self,
        *,
        indice_desde: Optional[int] = None,
        indice_hasta: Optional[int] = None,
        limite: int = 100_000,
    ) -> list[dict]:
        """Asientos en orden de REGISTRO (indice ASC) para verificar la cadena.

        La cadena se construye por índice (hash_previo = hash del asiento
        anterior por índice), no por fecha contable. Verificar en orden de
        fecha produce falsos positivos cuando hay backdating: la fecha de
        devengo es un atributo del registro, no su posición en el log.

        El orden cronológico-contable sigue siendo responsabilidad de
        listar(), listar_diario() y los informes.
        """
        where = ["empresa_id = %s"]
        params: list = [self._empresa_id]
        if indice_desde is not None:
            where.append("indice >= %s"); params.append(indice_desde)
        if indice_hasta is not None:
            where.append("indice <= %s"); params.append(indice_hasta)
        sql = (
            "SELECT indice, hash_previo, hash "
            "FROM asiento_contable WHERE " + " AND ".join(where) +
            " ORDER BY indice ASC LIMIT %s"
        )
        params.append(limite)
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchall()

    def verificar_cadena(
        self,
        desde: Optional[int] = None,
        hasta: Optional[int] = None,
    ) -> ReporteCadenaAsientos:
        asientos = self._listar_cadena(
            indice_desde=desde, indice_hasta=hasta, limite=100_000,
        )
        if not asientos:
            return ReporteCadenaAsientos(
                empresa_id=self._empresa_id,
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
            empresa_id=self._empresa_id,
            desde=asientos[0]["indice"], hasta=asientos[-1]["indice"],
            total=len(asientos),
            cadena_valida=len(roturas) == 0, roturas=roturas,
        )
