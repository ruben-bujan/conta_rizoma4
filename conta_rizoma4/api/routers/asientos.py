# -*- coding: utf-8 -*-
"""Endpoints de asientos."""
from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

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
    limite: int = 100,
):
    try:
        repo = RepositorioAsiento(empresa_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return repo.listar(indice_desde=desde, indice_hasta=hasta, limite=limite)


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

    # Verificar que el acto existe en el catálogo
    try:
        _, fn = obtener_acto(entrada.codigo_acto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Calcular siguiente índice y hash previo
    ultimo = repo.ultimo_indice()
    ultimo_data = repo.obtener(ultimo) if ultimo >= 0 else None
    from ...operativo.asiento import GENESIS
    hash_previo = ultimo_data["hash"] if ultimo_data else GENESIS
    indice = ultimo + 1

    # Crear el acto (el dispatcher del catálogo)
    params = dict(entrada.parametros)
    params.update({
        "indice": indice,
        "hash_previo": hash_previo,
        "fecha": entrada.fecha,
        "concepto": entrada.concepto,
    })
    # Añadir creado_por si el acto lo acepta
    try:
        acto = fn(**params, creado_por=entrada.creado_por)
    except TypeError:
        # Algunos actos no aceptan creado_por
        acto = fn(**params)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Persistir
    from ...partida_doble.persistencia import guardar_asiento
    guardar_asiento(acto, empresa_id=entrada.empresa_id)

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
