# -*- coding: utf-8 -*-
"""Endpoints de empresas y administración de sus casos RIZOMA4 asociados."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from ..schemas import EmpresaOut, CasoRizoma4In
from ..rizoma4_client import ClienteRizoma4, Rizoma4Error
from ...config import get_config, get_empresa, ConfigError
from ...custodia.casos_rizoma4 import (
    RepositorioCasoRizoma4, CasoRizoma4Error, validar_caso_id,
)
from ...dominio.adaptadores import RepositorioINCIVSALectura
from .auth import requerir_usuario
from ...config.postgresql import PG_URL
from typing import Optional

router = APIRouter(prefix="/empresas", tags=["empresas"])


def _exigir_admin(usuario: dict) -> None:
    if usuario.get("rol") != "admin":
        raise HTTPException(status_code=403, detail="Se requiere rol admin")


def _autorizar_empresa(empresa_id: str, usuario: dict) -> None:
    if usuario.get("rol") != "admin" and usuario.get("empresa_id") != empresa_id:
        raise HTTPException(status_code=403, detail="No tiene acceso a esta empresa")


@router.get("", response_model=list[EmpresaOut])
def listar_empresas(usuario: dict = Depends(requerir_usuario)):
    cfg = get_config()
    if usuario.get("rol") == "admin":
        return [e.a_dict() for e in cfg.empresas.values()]
    empresa_id = usuario.get("empresa_id")
    empresa = cfg.empresas.get(empresa_id)
    return [empresa.a_dict()] if empresa is not None else []


@router.get("/{empresa_id}", response_model=EmpresaOut)
def obtener_empresa(empresa_id: str, usuario: dict = Depends(requerir_usuario)):
    _autorizar_empresa(empresa_id, usuario)
    try:
        e = get_empresa(empresa_id)
    except ConfigError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return e.a_dict()


@router.get("/{empresa_id}/importaciones/incivsa")
def listar_lotes_incivsa(
    empresa_id: str,
    usuario: dict = Depends(requerir_usuario),
    limite: int = Query(50, ge=1, le=200),
):
    _autorizar_empresa(empresa_id, usuario)
    try:
        return RepositorioINCIVSALectura(PG_URL).listar_lotes(empresa_id, limite)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="No se pudieron consultar los lotes INCIVSA") from exc


@router.get("/{empresa_id}/importaciones/incivsa/{lote_id}")
def obtener_lote_incivsa(
    empresa_id: str,
    lote_id: str,
    usuario: dict = Depends(requerir_usuario),
):
    _autorizar_empresa(empresa_id, usuario)
    try:
        lote = RepositorioINCIVSALectura(PG_URL).obtener_lote(empresa_id, lote_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="No se pudo consultar el lote INCIVSA") from exc
    if lote is None:
        raise HTTPException(status_code=404, detail="Lote no encontrado para esta empresa")
    return lote


@router.get("/{empresa_id}/importaciones/incivsa/{lote_id}/grupos")
def listar_grupos_incivsa(
    empresa_id: str,
    lote_id: str,
    usuario: dict = Depends(requerir_usuario),
    estado: Optional[str] = Query(None),
    limite: int = Query(50, ge=1, le=200),
    desplazamiento: int = Query(0, ge=0),
):
    _autorizar_empresa(empresa_id, usuario)
    estados = {
        "PROPUESTA_BORRADOR", "NO_DETERMINADO_PRECISION_O_LINEA",
        "NO_DETERMINADO_FECHA", "NO_DETERMINADO_DESCUADRE",
    }
    if estado is not None and estado not in estados:
        raise HTTPException(status_code=422, detail="Estado de grupo INCIVSA no admitido")
    try:
        repo = RepositorioINCIVSALectura(PG_URL)
        if repo.obtener_lote(empresa_id, lote_id) is None:
            raise HTTPException(status_code=404, detail="Lote no encontrado para esta empresa")
        grupos = repo.listar_grupos(
            empresa_id, lote_id, estado=estado, limite=limite,
            desplazamiento=desplazamiento,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="No se pudieron consultar los grupos INCIVSA") from exc
    return {"lote_id": lote_id, "total_pagina": len(grupos), "grupos": grupos}


@router.get("/{empresa_id}/casos-rizoma4/disponibles")
def listar_casos_disponibles(
    empresa_id: str,
    usuario: dict = Depends(requerir_usuario),
):
    """Proxy administrativo del catálogo de casos visible desde RIZOMA4."""
    _exigir_admin(usuario)
    try:
        casos = ClienteRizoma4().listar_casos()
    except Rizoma4Error as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"empresa_id": empresa_id, "total": len(casos), "casos": casos}


@router.get("/{empresa_id}/casos-rizoma4")
def listar_casos_asociados(
    empresa_id: str,
    usuario: dict = Depends(requerir_usuario),
):
    _autorizar_empresa(empresa_id, usuario)
    try:
        casos = RepositorioCasoRizoma4().listar(empresa_id, solo_activos=True)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"No se pudo consultar la asociación empresa-caso: {exc}")
    return {"empresa_id": empresa_id, "total": len(casos), "casos": casos}


@router.post("/{empresa_id}/casos-rizoma4", status_code=201)
def asociar_caso(
    empresa_id: str,
    entrada: CasoRizoma4In,
    usuario: dict = Depends(requerir_usuario),
):
    _exigir_admin(usuario)
    try:
        caso_id = validar_caso_id(entrada.caso_id)
    except CasoRizoma4Error as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # No se permite registrar IDs inventados: el caso debe aparecer en el
    # catálogo que RIZOMA4 expone a la credencial de integración.
    try:
        casos = ClienteRizoma4().listar_casos()
    except Rizoma4Error as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    if not any(c.get("caso_id") == caso_id for c in casos):
        raise HTTPException(status_code=404, detail=f"El caso {caso_id!r} no existe o no es visible en RIZOMA4")

    try:
        return RepositorioCasoRizoma4().asociar(
            empresa_id=empresa_id,
            caso_id=caso_id,
            actor=str(usuario.get("sub") or usuario.get("usuario_id") or "admin"),
        )
    except CasoRizoma4Error as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"No se pudo guardar la asociación: {exc}")


@router.delete("/{empresa_id}/casos-rizoma4/{caso_id}")
def desasociar_caso(
    empresa_id: str,
    caso_id: str,
    usuario: dict = Depends(requerir_usuario),
):
    _exigir_admin(usuario)
    try:
        resultado = RepositorioCasoRizoma4().desasociar(
            empresa_id=empresa_id,
            caso_id=caso_id,
            actor=str(usuario.get("sub") or usuario.get("usuario_id") or "admin"),
        )
    except CasoRizoma4Error as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"No se pudo desactivar la asociación: {exc}")
    if resultado is None:
        raise HTTPException(status_code=404, detail="La asociación activa no existe")
    return resultado
