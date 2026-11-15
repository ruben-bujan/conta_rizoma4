# -*- coding: utf-8 -*-
"""Modelos Pydantic para la API."""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class EmpresaOut(BaseModel):
    empresa_id: str
    nombre: str
    moneda_funcional: str
    marco_contable: str
    pais: str
    grupo: str
    participacion_matriz: float
    ejercicio_inicio: str
    ejercicio_fin: str


class LineaOut(BaseModel):
    cuenta_pgc: str
    debe_centimos: int
    haber_centimos: int
    parrafo_pgc_id: Optional[int] = None
    concepto_linea: Optional[str] = None


class AsientoOut(BaseModel):
    indice: int
    fecha: date
    concepto: str
    lineas: list[LineaOut]
    hash_previo: str
    hash: str
    metadatos: dict = Field(default_factory=dict)


class AsientoIn(BaseModel):
    empresa_id: str
    codigo_acto: str  # ej. A_FACT_EMIT_SERV_NAC_SIN_RET
    fecha: date
    concepto: str
    creado_por: str
    parametros: dict = Field(
        default_factory=dict,
        description="Parámetros del acto (base_centimos, iva_pct, etc.)",
    )


class VerificarIn(BaseModel):
    empresa_id: str
    desde: Optional[int] = None
    hasta: Optional[int] = None


class VerificarOut(BaseModel):
    empresa_id: str
    desde: int
    hasta: int
    total: int
    cadena_valida: bool
    roturas: list[dict]
