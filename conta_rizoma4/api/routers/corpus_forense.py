# -*- coding: utf-8 -*-
"""API del corpus forense."""
from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...corpus_forense.modelo import (
    Dano, Expediente, Flujo, Sujeto, calcular_dano,
)
from ...corpus_forense.repositorios import (
    RepositorioSujeto, RepositorioExpediente, RepositorioFlujo,
    RepositorioDano,
)
from ...corpus_forense.agregacion import agregar_corpus, detectar_patrones
from .auth import requerir_usuario, requerir_roles


# El corpus todavía no tiene aislamiento por empresa. Hasta que se modele ese
# límite, se restringe a administradores; roles operativos no deben ver ni
# alterar expedientes potencialmente sensibles.
router = APIRouter(
    prefix="/corpus", tags=["corpus_forense"],
    dependencies=[Depends(requerir_roles("admin"))],
)


# ─── Modelos Pydantic ────────────────────────────────────────────

class SujetoIn(BaseModel):
    sujeto_id: str
    tipo: str
    nombre: str
    nif: Optional[str] = None
    sector: Optional[str] = None


class ExpedienteIn(BaseModel):
    expediente_id: str
    sujeto_id: str
    contrato_publico_ref: Optional[str] = None
    tipo_contrato: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    via_u1: Optional[str] = None
    es_punta_de_lanza: bool = False
    estado_concurso: str = "ninguno"
    seccion_sexta: bool = False
    calificacion: Optional[str] = None
    incidente_concursal_por_no_diligencia: bool = False
    buena_fe_acreditada: bool = False
    medio_prueba_buena_fe: Optional[str] = None
    nivel_vida_antes_centimos: Optional[int] = None
    nivel_vida_despues_centimos: Optional[int] = None
    porcentaje_menoscabo: Optional[float] = None
    quiebra_modo_vida: bool = False


class FlujoIn(BaseModel):
    expediente_id: str
    fecha: date
    concepto: str
    importe_centimos: int
    categoria: str
    documento_ref: Optional[str] = None


# ─── Sujetos ─────────────────────────────────────────────────────

@router.post("/sujetos", status_code=201)
def crear_sujeto(
    entrada: SujetoIn,
    usuario: dict = Depends(requerir_usuario),
):
    s = Sujeto(**entrada.model_dump())
    return RepositorioSujeto().crear(s).__dict__


@router.get("/sujetos")
def listar_sujetos(
    tipo: Optional[str] = None,
    usuario: dict = Depends(requerir_usuario),
):
    return RepositorioSujeto().listar(tipo)


@router.get("/sujetos/{sujeto_id}")
def obtener_sujeto(
    sujeto_id: str,
    usuario: dict = Depends(requerir_usuario),
):
    d = RepositorioSujeto().obtener(sujeto_id)
    if d is None:
        raise HTTPException(status_code=404, detail="Sujeto no encontrado")
    return d


# ─── Expedientes ────────────────────────────────────────────────

@router.post("/expedientes", status_code=201)
def crear_expediente(
    entrada: ExpedienteIn,
    usuario: dict = Depends(requerir_usuario),
):
    e = Expediente(**entrada.model_dump())
    return RepositorioExpediente().crear(e).__dict__


@router.get("/expedientes")
def listar_expedientes(
    universo: Optional[str] = Query(None, description="U1|U2|U3|no_victima"),
    sujeto_id: Optional[str] = None,
    usuario: dict = Depends(requerir_usuario),
):
    return RepositorioExpediente().listar(universo, sujeto_id)


@router.get("/expedientes/{expediente_id}")
def obtener_expediente(
    expediente_id: str,
    usuario: dict = Depends(requerir_usuario),
):
    d = RepositorioExpediente().obtener(expediente_id)
    if d is None:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    return d


# ─── Flujos ─────────────────────────────────────────────────────

@router.post("/flujos", status_code=201)
def crear_flujo(
    entrada: FlujoIn,
    usuario: dict = Depends(requerir_usuario),
):
    f = Flujo(id=0, **entrada.model_dump())
    return RepositorioFlujo().crear(f).__dict__


@router.get("/expedientes/{expediente_id}/flujos")
def listar_flujos(
    expediente_id: str,
    usuario: dict = Depends(requerir_usuario),
):
    return RepositorioFlujo().listar(expediente_id)


# ─── Daño ────────────────────────────────────────────────────────

@router.post("/expedientes/{expediente_id}/calcular-dano")
def calcular_dano_endpoint(
    expediente_id: str,
    fecha_corte: date = Query(..., description="Fecha de corte (YYYY-MM-DD)"),
    usuario: dict = Depends(requerir_usuario),
):
    repo_e = RepositorioExpediente()
    e = repo_e.obtener(expediente_id)
    if e is None:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    flujos = RepositorioFlujo().listar(expediente_id)
    exp = Expediente(**{k: v for k, v in e.items()
                        if k in Expediente.__dataclass_fields__})
    fl = [
        Flujo(id=f["id"], expediente_id=f["expediente_id"],
              fecha=f["fecha"], concepto=f["concepto"],
              importe_centimos=f["importe_centimos"],
              categoria=f["categoria"], documento_ref=f["documento_ref"],
              hash_previo=f["hash_previo"], hash=f["hash"])
        for f in flujos
    ]
    d = calcular_dano(exp, fl, fecha_corte)
    RepositorioDano().crear(d)
    return {
        "expediente_id": d.expediente_id,
        "principal_debido_centimos": d.principal_debido_centimos,
        "interes_renunciado_centimos": d.interes_renunciado_centimos,
        "interes_compuesto_centimos": d.interes_compuesto_centimos,
        "dano_total_centimos": d.dano_total_centimos,
        "fecha_corte": d.fecha_corte.isoformat(),
    }


@router.get("/expedientes/{expediente_id}/dano")
def obtener_dano(
    expediente_id: str,
    usuario: dict = Depends(requerir_usuario),
):
    d = RepositorioDano().obtener(expediente_id)
    if d is None:
        raise HTTPException(status_code=404, detail="Daño no calculado")
    return d


# ─── Agregación ──────────────────────────────────────────────────

@router.get("/agregado")
def agregado(
    universo: Optional[str] = None,
    usuario: dict = Depends(requerir_usuario),
):
    return agregar_corpus(universo)


@router.get("/patrones")
def patrones(
    usuario: dict = Depends(requerir_usuario),
):
    return detectar_patrones()
