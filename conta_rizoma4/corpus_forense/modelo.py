# -*- coding: utf-8 -*-
"""Modelo del corpus forense."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


class CorpusError(Exception):
    pass


@dataclass(frozen=True)
class Sujeto:
    sujeto_id: str
    tipo: str  # "MIPYME" | "FISICA"
    nombre: str
    nif: Optional[str] = None
    sector: Optional[str] = None
    anonimizado: bool = True
    metadatos: dict = field(default_factory=dict)


@dataclass
class Expediente:
    expediente_id: str
    sujeto_id: str
    contrato_publico_ref: Optional[str] = None
    tipo_contrato: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None

    via_u1: Optional[str] = None
    es_punta_de_lanza: bool = False

    estado_concurso: str = "ninguno"
    fecha_concurso: Optional[date] = None
    fecha_conclusion: Optional[date] = None
    seccion_sexta: bool = False
    calificacion: Optional[str] = None
    incidente_concursal_por_no_diligencia: bool = False

    buena_fe_acreditada: bool = False
    medio_prueba_buena_fe: Optional[str] = None

    nivel_vida_antes_centimos: Optional[int] = None
    nivel_vida_despues_centimos: Optional[int] = None
    porcentaje_menoscabo: Optional[float] = None
    quiebra_modo_vida: bool = False

    universo: Optional[str] = None
    tipo_reparacion: Optional[str] = None
    metadatos: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Flujo:
    id: int
    expediente_id: str
    fecha: date
    concepto: str
    importe_centimos: int
    categoria: str
    documento_ref: Optional[str] = None
    hash_previo: str = ""
    hash: str = ""


@dataclass(frozen=True)
class Dano:
    expediente_id: str
    principal_debido_centimos: int
    interes_renunciado_centimos: int
    interes_compuesto_centimos: int
    dano_moral_centimos: int
    consecuencias_indirectas_centimos: int
    dano_total_centimos: int
    fecha_corte: date


# ─── Lógica de clasificación (R1-R5) ──────────────────────────

def _concurso_ok(exp: Expediente) -> bool:
    """R2: el concurso es válido para U1."""
    if exp.estado_concurso == "ninguno":
        return False
    # Cualquier estado del concurso es válido
    if exp.estado_concurso not in ("presentado", "presumido", "caido", "recaydo"):
        return False
    # R2: si hay sección sexta, la calificación debe ser fortuito
    if exp.seccion_sexta and exp.calificacion != "fortuito":
        return False
    return True


def _diligente(exp: Expediente) -> bool:
    """R3: la diligencia se presume. Solo se rompe si incidente concursal."""
    return not exp.incidente_concursal_por_no_diligencia


def _relevante(exp: Expediente) -> bool:
    """R4: menoscabo >= 20% es relevante."""
    if exp.porcentaje_menoscabo is None:
        return False
    return exp.porcentaje_menoscabo >= 20.0


def _calcular_porcentaje(exp: Expediente) -> Optional[float]:
    """Calcula el porcentaje de menoscabo si no está precalculado."""
    if exp.porcentaje_menoscabo is not None:
        return exp.porcentaje_menoscabo
    if exp.nivel_vida_antes_centimos is None or exp.nivel_vida_despues_centimos is None:
        return None
    if exp.nivel_vida_antes_centimos <= 0:
        return None
    diff = exp.nivel_vida_antes_centimos - exp.nivel_vida_despues_centimos
    return (diff / exp.nivel_vida_antes_centimos) * 100.0


def clasificar_expediente(exp: Expediente) -> tuple[str, str]:
    """Clasifica el expediente en U1/U2/U3/no_victima.

    Devuelve (universo, tipo_reparacion).
    """
    pct = _calcular_porcentaje(exp)
    exp.porcentaje_menoscabo = pct

    concurso_ok = _concurso_ok(exp)
    diligente = _diligente(exp)
    relevante = pct is not None and pct >= 20.0

    # U1: concurso + buena fe + diligente + relevante
    if concurso_ok and exp.buena_fe_acreditada and diligente and relevante:
        return "U1", "restiucion_in_integrum_maxima"

    # U2: sin concurso (o concurso no ok) + buena fe + relevante
    if exp.buena_fe_acreditada and relevante and not concurso_ok:
        return "U2", "indemnizacion_dano_relevante"

    # U2: concurso no ok + buena fe + relevante
    if exp.buena_fe_acreditada and relevante and concurso_ok is False:
        return "U2", "indemnizacion_dano_relevante"

    # U3: sin relevancia
    if exp.buena_fe_acreditada and not relevante:
        return "U3", "sin_reparacion"

    return "no_victima", "sin_reparacion"


# ─── Cálculo del daño ─────────────────────────────────────────

def calcular_dano(
    exp: Expediente,
    flujos: list[Flujo],
    fecha_corte: date,
    tasa_interes: float = 0.07,
) -> Dano:
    """Calcula el daño de un expediente.

    Componentes:
      - principal_debido: suma de flujos impagados (facturas - cobros)
      - interes_renunciado: 7% × principal × tiempo hasta la renuncia
      - interes_compuesto: 7% anual sobre el principal hasta fecha_corte
      - dano_moral: 0 (se calcula aparte si procede)
      - consecuencias_indirectas: 0 (solo U1, se calcula aparte)
    """
    # Principal debido: facturas - cobros
    principal = 0
    fecha_renuncia = None
    for f in flujos:
        if f.categoria in ("factura", "requerimiento"):
            principal += f.importe_centimos
        elif f.categoria in ("cobro_principal", "cobro_interes"):
            principal -= abs(f.importe_centimos)
        elif f.categoria == "renuncia_interes":
            fecha_renuncia = f.fecha

    if principal < 0:
        principal = 0

    # Interés renunciado: 7% × principal × tiempo hasta la renuncia
    interes_renunciado = 0
    if fecha_renuncia and principal > 0:
        dias = (fecha_renuncia - exp.fecha_inicio).days if exp.fecha_inicio else 0
        if dias > 0:
            interes_renunciado = int(principal * tasa_interes * dias / 365)

    # Interés compuesto: 7% anual desde la renuncia hasta fecha_corte
    interes_compuesto = 0
    if fecha_renuncia and principal > 0:
        dias = (fecha_corte - fecha_renuncia).days
        if dias > 0:
            # Interés compuesto anual
            anos = dias / 365
            factor = (1 + tasa_interes) ** anos
            interes_compuesto = int(principal * (factor - 1))

    # Daño total
    dano_total = (
        principal + interes_renunciado + interes_compuesto
    )

    return Dano(
        expediente_id=exp.expediente_id,
        principal_debido_centimos=principal,
        interes_renunciado_centimos=interes_renunciado,
        interes_compuesto_centimos=interes_compuesto,
        dano_moral_centimos=0,
        consecuencias_indirectas_centimos=0,
        dano_total_centimos=dano_total,
        fecha_corte=fecha_corte,
    )
