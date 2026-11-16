# -*- coding: utf-8 -*-
"""Modelo de custodia: obras, operarios, leases, documentos."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


class CustodiaError(Exception):
    """Error en el proceso de custodia."""


@dataclass(frozen=True)
class Obra:
    obra_id: str
    empresa_id: str
    nombre: str
    cliente_nif: Optional[str] = None
    presupuesto_centimos: Optional[int] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    estado: str = "activa"
    config_sync: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Operario:
    operario_id: str
    empresa_id: str
    nombre: str
    rol: str  # "aux_obra" | "jefe_obra" | "jefe_prod" | "central" | "auditor"
    email: Optional[str] = None
    certificado: Optional[str] = None
    activo: bool = True


@dataclass(frozen=True)
class Lease:
    lease_id: str
    empresa_id: str
    obra_id: Optional[str]
    tipo: str  # "asiento" | "visado"
    indice_reservado: int
    operario: str
    estado: str  # "CONCEDIDO" | "USADO" | "EXPIRADO" | "CANCELADO"
    creado_en: datetime
    expira_en: datetime
    renovado_en: Optional[datetime] = None
    usado_en: Optional[datetime] = None


@dataclass(frozen=True)
class Documento:
    id: int
    empresa_id: str
    obra_id: Optional[str]
    hash_cas: str
    tipo: str
    nombre: Optional[str]
    tamano_bytes: Optional[int]
    subido_por: Optional[str]
