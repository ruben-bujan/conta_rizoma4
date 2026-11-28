#!/usr/bin/env python3
"""Incorpora la fuente INCIVSA en borrador, sin borrar ni acreditar el origen."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from pilot_incivsa.constructor_memoria import (
    CSV_IN,
    EMPRESA_HEREDADA,
    GrupoOrigen,
    ResultadoConstructor,
    _parse_fecha,
    construir_desde_csv,
)
PARSER_VERSION = "incivsa-decimal-v1"
GENESIS = "0" * 64
DDL = Path(__file__).resolve().parent.parent / "migrations" / "006_incivsa_importacion.sql"


class ErrorIncorporacionINCIVSA(RuntimeError):
    pass


def calcular_huella(contenido: dict[str, Any]) -> str:
    canonico = json.dumps(contenido, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()


def calcular_hash(huella: str, previo: str, indice: int) -> str:
    return hashlib.sha256(f"{previo}|{huella}|{indice}".encode("utf-8")).hexdigest()


def _lote_id(sha_fuente: str) -> str:
    return hashlib.sha256(
        f"{EMPRESA_HEREDADA}|{sha_fuente}|{PARSER_VERSION}".encode("utf-8")
    ).hexdigest()


def _clave_grupo(grupo: GrupoOrigen) -> str:
    return hashlib.sha256(grupo.clave_origen.encode("utf-8")).hexdigest()


def _contenido_hash(
    *, fecha, concepto: str, lineas: tuple, metadatos: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    filas = [
        {
            "cuenta_pgc": linea.cuenta,
            "debe_centimos": linea.debe_centimos,
            "haber_centimos": linea.haber_centimos,
            "parrafo_pgc_id": None,
            "concepto_linea": linea.persona,
        }
        for linea in lineas
    ]
    contenido = {
        "fecha": fecha.isoformat(),
        "concepto": concepto,
        "lineas": filas,
        "metadatos": metadatos,
    }
    return contenido, filas


def incorporar(
    conexion, *, ruta_csv: Path = CSV_IN, confirmar: bool = False,
) -> dict[str, Any]:
    """Escribe lote y borradores atómicamente; por defecto verifica y revierte."""
    sha_fuente = hashlib.sha256(ruta_csv.read_bytes()).hexdigest()
    resultado: ResultadoConstructor = construir_desde_csv(ruta_csv)
    if len(resultado.grupos_origen) != resultado.grupos_totales:
        raise ErrorIncorporacionINCIVSA("El parser no conservó todos los grupos de origen")
    grupos = sorted(resultado.grupos_origen, key=lambda g: (g.codigo_origen, g.fecha_origen))
    # Las fechas del constructor se normalizan; la clave fuente permanece textual.
    por_clave = {
        g.clave_origen: next(
            (
                a for a in resultado.asientos
                if a.codigo_origen == g.codigo_origen
                and a.fecha.date() == _parse_fecha(g.fecha_origen).date()
            ),
            None,
        )
        for g in grupos
    }
    candidatos = [g for g in grupos if g.estado_migracion == "CANDIDATO_CUADRADO"]
    if any(por_clave[g.clave_origen] is None for g in candidatos):
        raise ErrorIncorporacionINCIVSA("No se pudo vincular un grupo cuadrado a su asiento propuesto")
    no_determinados = len(grupos) - len(candidatos)
    total_filas = sum(len(grupo.filas_originales) for grupo in grupos)
    lineas_esperadas = sum(len(por_clave[g.clave_origen].lineas) for g in candidatos)
    lote_id = _lote_id(sha_fuente)

    from psycopg.types.json import Jsonb

    try:
        with conexion.cursor() as cur:
            cur.execute(DDL.read_text(encoding="utf-8"))
            # Mismo lock que el repositorio contable: evita que el lote migre
            # índices mientras otra operación crea/revierte asientos INCIVSA.
            cur.execute(
                "SELECT pg_advisory_xact_lock(741521, hashtext(%s))",
                (EMPRESA_HEREDADA,),
            )
            cur.execute(
                "SELECT lote_id, version_parser FROM incivsa_lote_importacion "
                "WHERE empresa_id = %s AND sha256_fuente = %s",
                (EMPRESA_HEREDADA, sha_fuente),
            )
            existente = cur.fetchone()
            if existente:
                if existente[0].strip() != lote_id or existente[1] != PARSER_VERSION:
                    raise ErrorIncorporacionINCIVSA(
                        "La fuente ya existe con otra versión; no se duplica ni sobrescribe"
                    )
                cur.execute(
                    "SELECT COUNT(*), "
                    "COUNT(*) FILTER (WHERE estado_migracion = 'PROPUESTA_BORRADOR'), "
                    "COUNT(*) FILTER (WHERE starts_with(estado_migracion, 'NO_DETERMINADO')), "
                    "COALESCE(SUM(jsonb_array_length(filas_origen)), 0) "
                    "FROM incivsa_grupo_origen WHERE lote_id = %s",
                    (lote_id,),
                )
                conteos = cur.fetchone()
                if conteos != (len(grupos), len(candidatos), no_determinados, total_filas):
                    raise ErrorIncorporacionINCIVSA("El lote previo está incompleto; requiere revisión")
                conexion.rollback()
                return {
                    "lote_id": lote_id, "sha256_fuente": sha_fuente,
                    "grupos": len(grupos), "propuestas_borrador": len(candidatos),
                    "filas_origen": total_filas, "no_determinados": no_determinados, "ya_existia": True,
                    "confirmado": False, "rollback": True,
                }

            cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                        (f"incivsa:{EMPRESA_HEREDADA}",))
            cur.execute(
                "SELECT indice, hash FROM asiento_contable WHERE empresa_id = %s "
                "ORDER BY indice DESC LIMIT 1",
                (EMPRESA_HEREDADA,),
            )
            ultimo = cur.fetchone()
            siguiente_indice = (ultimo[0] + 1) if ultimo else 0
            hash_previo = ultimo[1] if ultimo else GENESIS

            cur.execute(
                "INSERT INTO incivsa_lote_importacion "
                "(lote_id, empresa_id, fuente, sha256_fuente, version_parser, "
                "total_grupos, total_filas_origen, grupos_propuestos, grupos_no_determinados) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (lote_id, EMPRESA_HEREDADA, ruta_csv.name, sha_fuente, PARSER_VERSION,
                 len(grupos), total_filas, len(candidatos), no_determinados),
            )

            indices: dict[str, int] = {}
            for grupo in candidatos:
                asiento = por_clave[grupo.clave_origen]
                indice = siguiente_indice
                siguiente_indice += 1
                meta = {
                    "lote_importacion": lote_id,
                    "fuente_sha256": sha_fuente,
                    "empresa_funcional": "INCIVSA",
                    "empresa_origen": EMPRESA_HEREDADA,
                    "codigo_asiento_origen": grupo.codigo_origen,
                    "fecha_origen": grupo.fecha_origen,
                    "estado_epistemologico": "NO_DETERMINADO",
                    "estado_migracion": "IMPORTADO_SIN_ACREDITACION_EPISTEMICA",
                }
                contenido, lineas_hash = _contenido_hash(
                    fecha=asiento.fecha.date(), concepto=asiento.concepto,
                    lineas=asiento.lineas, metadatos=meta,
                )
                huella = calcular_huella(contenido)
                hash_actual = calcular_hash(huella, hash_previo, indice)
                cur.execute(
                    "INSERT INTO asiento_contable "
                    "(indice, fecha, concepto, hash_previo, hash, metadatos, empresa_id, estado, "
                    "operario_creador, operario_visador, operario_aprobador, documento_ref) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, 'BORRADOR', NULL, NULL, NULL, NULL)",
                    (indice, asiento.fecha.date(), asiento.concepto, hash_previo,
                     hash_actual, Jsonb(meta), EMPRESA_HEREDADA),
                )
                for linea, linea_hash in zip(asiento.lineas, lineas_hash, strict=True):
                    cur.execute(
                        "INSERT INTO linea_asiento "
                        "(asiento_indice, cuenta_pgc, debe_centimos, haber_centimos, "
                        "parrafo_pgc_id, concepto_linea, empresa_id) "
                        "VALUES (%s, %s, %s, %s, NULL, %s, %s)",
                        (indice, linea.cuenta, linea.debe_centimos,
                         linea.haber_centimos, linea.persona, EMPRESA_HEREDADA),
                    )
                indices[grupo.clave_origen] = indice
                hash_previo = hash_actual

            for grupo in grupos:
                estado = (
                    "PROPUESTA_BORRADOR" if grupo.estado_migracion == "CANDIDATO_CUADRADO"
                    else grupo.estado_migracion
                )
                propuesta = [
                    {
                        "cuenta": l.cuenta, "debe_centimos": l.debe_centimos,
                        "haber_centimos": l.haber_centimos,
                    }
                    for l in grupo.lineas
                ]
                cur.execute(
                    "INSERT INTO incivsa_grupo_origen "
                    "(lote_id, empresa_id, clave_origen_sha256, codigo_origen, fecha_origen, "
                    "estado_migracion, filas_origen, lineas_propuestas, error_origen, asiento_indice) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (lote_id, EMPRESA_HEREDADA, _clave_grupo(grupo),
                     grupo.codigo_origen, grupo.fecha_origen, estado,
                     Jsonb([list(f) for f in grupo.filas_originales]),
                     Jsonb(propuesta), grupo.error, indices.get(grupo.clave_origen)),
                )

            cur.execute(
                "SELECT COUNT(*), COUNT(*) FILTER (WHERE estado_migracion = 'PROPUESTA_BORRADOR'), "
                "COUNT(*) FILTER (WHERE starts_with(estado_migracion, 'NO_DETERMINADO')) "
                ", COALESCE(SUM(jsonb_array_length(filas_origen)), 0) "
                "FROM incivsa_grupo_origen WHERE lote_id = %s",
                (lote_id,),
            )
            verificadas = cur.fetchone()
            if verificadas != (len(grupos), len(candidatos), no_determinados, total_filas):
                raise ErrorIncorporacionINCIVSA("Los conteos del lote no superan la verificación")
            cur.execute(
                "SELECT COUNT(*), COUNT(*) FILTER (WHERE a.estado <> 'BORRADOR'), "
                "COUNT(*) FILTER (WHERE a.indice IS NULL OR a.hash IS NULL) "
                "FROM incivsa_grupo_origen g LEFT JOIN asiento_contable a "
                "ON a.empresa_id = g.empresa_id AND a.indice = g.asiento_indice "
                "WHERE g.lote_id = %s AND g.asiento_indice IS NOT NULL",
                (lote_id,),
            )
            asientos_verificados = cur.fetchone()
            if asientos_verificados != (len(candidatos), 0, 0):
                raise ErrorIncorporacionINCIVSA("Las propuestas no superan la verificación de asiento")
            cur.execute(
                "SELECT COUNT(*), "
                "COUNT(*) FILTER (WHERE debe_centimos <> haber_centimos), "
                "COALESCE(SUM(numero_lineas), 0) "
                "FROM (SELECT a.indice, COALESCE(SUM(l.debe_centimos), 0) AS debe_centimos, "
                "COALESCE(SUM(l.haber_centimos), 0) AS haber_centimos, COUNT(l.id) AS numero_lineas "
                "FROM asiento_contable a LEFT JOIN linea_asiento l "
                "ON l.empresa_id = a.empresa_id AND l.asiento_indice = a.indice "
                "WHERE a.empresa_id = %s AND a.metadatos->>'lote_importacion' = %s "
                "GROUP BY a.indice) verificacion",
                (EMPRESA_HEREDADA, lote_id),
            )
            lineas_verificadas = cur.fetchone()
            if lineas_verificadas != (len(candidatos), 0, lineas_esperadas):
                raise ErrorIncorporacionINCIVSA("Las líneas no superan cuadre o conteo")

        if confirmar:
            conexion.commit()
        else:
            conexion.rollback()
        return {
            "lote_id": lote_id, "sha256_fuente": sha_fuente,
            "grupos": len(grupos), "propuestas_borrador": len(candidatos),
            "filas_origen": total_filas, "no_determinados": no_determinados, "ya_existia": False,
            "confirmado": confirmar, "rollback": not confirmar,
        }
    except Exception:
        conexion.rollback()
        raise


def corregir_cadena_hash_lote(conexion, lote_id: str, *, confirmar: bool = False) -> dict[str, Any]:
    """Recalcula hashes de borradores recién migrados y registra el ajuste append-only."""
    try:
        with conexion.cursor() as cur:
            cur.execute(DDL.read_text(encoding="utf-8"))
            cur.execute(
                "SELECT grupos_propuestos FROM incivsa_lote_importacion "
                "WHERE lote_id = %s AND empresa_id = %s",
                (lote_id, EMPRESA_HEREDADA),
            )
            lote = cur.fetchone()
            if lote is None:
                raise ErrorIncorporacionINCIVSA("Lote inexistente")
            esperados = lote[0]
            cur.execute(
                "SELECT a.indice,a.fecha,a.concepto,a.hash_previo,a.hash,a.estado,"
                "a.operario_creador,a.operario_visador,a.operario_aprobador,a.documento_ref,"
                "a.metadatos,COALESCE(jsonb_agg(jsonb_build_object("
                "'cuenta_pgc',l.cuenta_pgc,'debe_centimos',l.debe_centimos,"
                "'haber_centimos',l.haber_centimos,'parrafo_pgc_id',l.parrafo_pgc_id,"
                "'concepto_linea',l.concepto_linea) ORDER BY l.id) "
                "FILTER (WHERE l.id IS NOT NULL),'[]'::jsonb) "
                "FROM asiento_contable a LEFT JOIN linea_asiento l "
                "ON l.empresa_id=a.empresa_id AND l.asiento_indice=a.indice "
                "WHERE a.empresa_id=%s AND a.metadatos->>'lote_importacion'=%s "
                "GROUP BY a.indice,a.fecha,a.concepto,a.hash_previo,a.hash,a.estado,"
                "a.operario_creador,a.operario_visador,a.operario_aprobador,a.documento_ref,a.metadatos "
                "ORDER BY a.indice",
                (EMPRESA_HEREDADA, lote_id),
            )
            filas = cur.fetchall()
            if len(filas) != esperados or any(
                f[5] != "BORRADOR" or any(f[i] is not None for i in (6, 7, 8, 9))
                for f in filas
            ):
                raise ErrorIncorporacionINCIVSA(
                    "El lote ya no es un conjunto aislado de borradores; no se modifica"
                )
            cur.execute(
                "SELECT COUNT(*) FROM asiento_contable WHERE empresa_id=%s "
                "AND (metadatos->>'lote_importacion' IS DISTINCT FROM %s)",
                (EMPRESA_HEREDADA, lote_id),
            )
            if cur.fetchone()[0] != 0:
                raise ErrorIncorporacionINCIVSA(
                    "Hay asientos ajenos al lote en la cadena; se requiere revisión manual"
                )

            previous = GENESIS
            correcciones: list[tuple[int, str, str, str, str]] = []
            for fila in filas:
                indice, fecha, concepto, hash_previo, hash_actual = fila[:5]
                metadatos, lineas = fila[10], fila[11]
                contenido = {
                    "fecha": fecha.isoformat(),
                    "concepto": concepto,
                    "lineas": lineas,
                    "metadatos": metadatos,
                }
                nuevo_hash = calcular_hash(calcular_huella(contenido), previous, indice)
                if hash_previo != previous or hash_actual != nuevo_hash:
                    correcciones.append((indice, hash_previo, hash_actual, previous, nuevo_hash))
                previous = nuevo_hash
            if not correcciones:
                conexion.rollback()
                return {
                    "lote_id": lote_id, "asientos_reencadenados": 0,
                    "ya_correcta": True, "confirmado": False, "rollback": True,
                }
            tip_anterior = filas[-1][4] if filas else GENESIS
            for indice, old_prev, old_hash, new_prev, new_hash in correcciones:
                cur.execute(
                    "UPDATE asiento_contable SET hash_previo=%s, hash=%s "
                    "WHERE empresa_id=%s AND indice=%s AND estado='BORRADOR' "
                    "AND metadatos->>'lote_importacion'=%s AND hash_previo=%s AND hash=%s",
                    (new_prev, new_hash, EMPRESA_HEREDADA, indice, lote_id, old_prev, old_hash),
                )
                if cur.rowcount != 1:
                    raise ErrorIncorporacionINCIVSA("Conflicto al corregir la cadena de hashes")
            cur.execute(
                "INSERT INTO incivsa_lote_evento "
                "(lote_id,tipo,descripcion,cantidad_afectada,hash_anterior,hash_resultante) "
                "VALUES (%s,'CADENA_HASH_NORMALIZADA',%s,%s,%s,%s)",
                (lote_id, "Hash recalculado usando la fecha contable DATE persistida; "
                 "contenido y líneas permanecen iguales.", len(correcciones),
                 tip_anterior, previous),
            )
            cur.execute(
                "SELECT COUNT(*) FROM asiento_contable WHERE empresa_id=%s "
                "AND metadatos->>'lote_importacion'=%s AND estado='BORRADOR'",
                (EMPRESA_HEREDADA, lote_id),
            )
            if cur.fetchone()[0] != esperados:
                raise ErrorIncorporacionINCIVSA("El conteo cambió durante la normalización")
        if confirmar:
            conexion.commit()
        else:
            conexion.rollback()
        return {
            "lote_id": lote_id, "asientos_reencadenados": len(correcciones),
            "hash_tip_anterior": tip_anterior, "hash_tip_resultante": previous,
            "confirmado": confirmar, "rollback": not confirmar,
        }
    except Exception:
        conexion.rollback()
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirmar", action="store_true",
                        help="confirma la transacción tras las verificaciones")
    parser.add_argument("--csv", type=Path, default=CSV_IN)
    args = parser.parse_args()
    import psycopg
    pg_url = os.environ.get("CONTA_PG_URL")
    if not pg_url:
        raise RuntimeError("Configura CONTA_PG_URL en el entorno (no la compartas por chat)")
    with psycopg.connect(pg_url) as conexion:
        reporte = incorporar(conexion, ruta_csv=args.csv, confirmar=args.confirmar)
    print(json.dumps(reporte, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
