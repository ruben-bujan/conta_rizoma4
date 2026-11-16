# -*- coding: utf-8 -*-
"""Endpoints de asientos."""
from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..schemas import AsientoIn, AsientoOut, LineaOut
from ...partida_doble import RepositorioAsiento
from ...partida_doble.backend import BackendPostgres
from ...actos.catalogo import obtener as obtener_acto


router = APIRouter(prefix="/asientos", tags=["asientos"])


@router.get("", response_model=list[AsientoOut])
def listar_asientos(
    empresa_id: str = Query(..., description="Empresa (obligatorio)"),
    desde: Optional[int] = None,
    hasta: Optional[int] = None,
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    limite: int = 100,
):
    try:
        repo = RepositorioAsiento(empresa_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    asientos = repo.listar(indice_desde=desde, indice_hasta=hasta, limite=limite)
    # Filtrar por estado si se pide
    if estado:
        import psycopg
        from ...partida_doble.persistencia import PG_URL
        with psycopg.connect(PG_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT indice FROM asiento_contable "
                    "WHERE empresa_id = %s AND estado = %s",
                    (empresa_id, estado),
                )
                indices_ok = {row[0] for row in cur.fetchall()}
        asientos = [a for a in asientos if a["indice"] in indices_ok]
    return asientos


@router.get("/{indice}", response_model=AsientoOut)
def obtener_asiento(
    indice: int,
    empresa_id: str = Query(..., description="Empresa (obligatorio)"),
):
    try:
        repo = RepositorioAsiento(empresa_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    d = repo.obtener(indice)
    if d is None:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")
    return d


@router.post("", response_model=AsientoOut, status_code=201)
def crear_asiento(entrada: AsientoIn):
    try:
        repo = RepositorioAsiento(entrada.empresa_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        _, fn = obtener_acto(entrada.codigo_acto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 1. Si hay lease, validarlo
    lease = None
    if entrada.lease_id:
        from ...custodia.repositorios import RepositorioLease
        from ...custodia.modelo import CustodiaError
        try:
            lease = RepositorioLease().obtener(entrada.lease_id)
        except Exception:
            lease = None
        if lease is None:
            raise HTTPException(status_code=409, detail="Lease no encontrado")
        if lease["estado"] != "CONCEDIDO":
            raise HTTPException(
                status_code=409,
                detail=f"Lease en estado {lease['estado']}",
            )

    # 2. Calcular índice y hash previo
    if lease:
        indice = lease["indice_reservado"]
    else:
        indice = repo.ultimo_indice() + 1
    ultimo_data = repo.obtener(indice - 1) if indice > 0 else None
    from ...operativo.asiento import GENESIS
    hash_previo = ultimo_data["hash"] if ultimo_data else GENESIS

    # 3. Crear acto
    params = dict(entrada.parametros)
    params.update({
        "indice": indice,
        "hash_previo": hash_previo,
        "fecha": entrada.fecha,
        "concepto": entrada.concepto,
    })
    try:
        acto = fn(**params, creado_por=entrada.creado_por)
    except TypeError:
        acto = fn(**params)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 4. Persistir (con campos de custodia)
    from ...partida_doble.persistencia import guardar_asiento
    guardar_asiento(acto, empresa_id=entrada.empresa_id)

    # 5. Actualizar campos de custodia en el asiento
    import psycopg
    from ...partida_doble.persistencia import PG_URL
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE asiento_contable
                SET obra_id = %s, operario_creador = %s,
                    lease_id = %s, estado = %s,
                    documento_ref = %s
                WHERE empresa_id = %s AND indice = %s
                """,
                (entrada.obra_id, entrada.creado_por,
                 entrada.lease_id, "BORRADOR",
                 entrada.documento_ref, entrada.empresa_id, indice),
            )
        conn.commit()

    # 6. Marcar lease como USADO
    if lease:
        from ...custodia.repositorios import RepositorioLease
        RepositorioLease().marcar_usado(entrada.lease_id)

    return {
        "indice": acto.indice,
        "fecha": acto.fecha,
        "concepto": acto.concepto,
        "lineas": [
            {
                "cuenta_pgc": l.cuenta_pgc,
                "debe_centimos": l.debe_centimos,
                "haber_centimos": l.haber_centimos,
                "parrafo_pgc_id": l.parrafo_pgc_id,
                "concepto_linea": l.concepto_linea,
            }
            for l in acto.lineas
        ],
        "hash_previo": acto.hash_previo,
        "hash": acto.hash,
        "metadatos": acto.metadatos,
    }


class VisarIn(BaseModel):
    operario_visador: str


class AprobarIn(BaseModel):
    operario_aprobador: str


class RizomizarIn(BaseModel):
    ok: bool
    alerta: Optional[str] = None
    documento_ref: Optional[str] = None


@router.post("/{indice}/visar")
def visar(indice: int, entrada: VisarIn, empresa_id: str = Query(...)):
    import psycopg
    from ...partida_doble.persistencia import PG_URL
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT estado FROM asiento_contable "
                "WHERE empresa_id = %s AND indice = %s",
                (empresa_id, indice),
            )
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Asiento no encontrado")
            if row[0] != "BORRADOR":
                raise HTTPException(
                    status_code=409,
                    detail=f"Asiento en estado {row[0]}, no BORRADOR",
                )
            cur.execute(
                "UPDATE asiento_contable SET estado = 'VISADO', "
                "operario_visador = %s "
                "WHERE empresa_id = %s AND indice = %s",
                (entrada.operario_visador, empresa_id, indice),
            )
        conn.commit()
    return {"ok": True, "estado": "VISADO"}


@router.post("/{indice}/aprobar")
def aprobar(indice: int, entrada: AprobarIn, empresa_id: str = Query(...)):
    import psycopg
    from ...partida_doble.persistencia import PG_URL
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT estado FROM asiento_contable "
                "WHERE empresa_id = %s AND indice = %s",
                (empresa_id, indice),
            )
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Asiento no encontrado")
            if row[0] != "VISADO":
                raise HTTPException(
                    status_code=409,
                    detail=f"Asiento en estado {row[0]}, no VISADO",
                )
            cur.execute(
                "UPDATE asiento_contable SET estado = 'APROBADO', "
                "operario_aprobador = %s "
                "WHERE empresa_id = %s AND indice = %s",
                (entrada.operario_aprobador, empresa_id, indice),
            )
        conn.commit()
    return {"ok": True, "estado": "APROBADO"}


@router.post("/{indice}/rizomizar")
def rizomizar(indice: int, entrada: RizomizarIn, empresa_id: str = Query(...)):
    import psycopg
    from ...partida_doble.persistencia import PG_URL
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT estado FROM asiento_contable "
                "WHERE empresa_id = %s AND indice = %s",
                (empresa_id, indice),
            )
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Asiento no encontrado")
            if row[0] != "APROBADO":
                raise HTTPException(
                    status_code=409,
                    detail=f"Asiento en estado {row[0]}, no APROBADO",
                )
            if entrada.ok:
                nuevo_estado = "RIZOMIZADO"
                alerta = None
            else:
                nuevo_estado = "EN_CUARENTENA"
                alerta = entrada.alerta or "Rizomización fallida"
            cur.execute(
                "UPDATE asiento_contable SET estado = %s, alerta = %s, "
                "documento_ref = COALESCE(%s, documento_ref) "
                "WHERE empresa_id = %s AND indice = %s",
                (nuevo_estado, alerta, entrada.documento_ref,
                 empresa_id, indice),
            )
        conn.commit()
    return {"ok": True, "estado": nuevo_estado}


@router.delete("/{indice}")
def borrar_asiento(
    indice: int,
    empresa_id: str = Query(..., description="Empresa (obligatorio)"),
):
    try:
        repo = RepositorioAsiento(empresa_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if repo.obtener(indice) is None:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")
    from ...partida_doble.persistencia import borrar_asiento as _borrar
    _borrar(indice, empresa_id=empresa_id)
    return {"ok": True}
