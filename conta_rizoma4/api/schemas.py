# -*- coding: utf-8 -*-
"""Modelos Pydantic para la API."""
from __future__ import annotations

from datetime import date, datetime
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
    caso_id: Optional[str] = None
    fecha: date
    concepto: str
    lineas: list[LineaOut]
    hash_previo: str
    hash: str
    metadatos: dict = Field(default_factory=dict)


class AsientoIn(BaseModel):
    empresa_id: str
    caso_id: str = Field(..., min_length=1, pattern=r"^[A-Za-z0-9_-]+$")
    codigo_acto: str
    fecha: date
    concepto: str
    creado_por: str
    parametros: dict = Field(
        default_factory=dict,
        description="Parámetros del acto (base_centimos, iva_pct, etc.)",
    )
    # Custodia (opcional; si se omite, se crea sin lease, BORRADOR)
    lease_id: Optional[str] = None
    obra_id: Optional[str] = None
    documento_ref: Optional[str] = None
    # H-15: Soporte para lista de referencias documentales N:M
    documentos_refs: list[str] = Field(default_factory=list, description="Lista de hashes de documentos asociados (N:M)")


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

class CasoRizoma4In(BaseModel):
    caso_id: str = Field(..., min_length=1, pattern=r"^[A-Za-z0-9_-]+$")


class CasoRizoma4Out(BaseModel):
    empresa_id: str
    caso_id: str
    activo: bool
    creado_por: str
    creado_en: Optional[datetime] = None
    modificado_por: str
    modificado_en: Optional[datetime] = None
    desactivado_en: Optional[datetime] = None
