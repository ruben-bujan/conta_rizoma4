# -*- coding: utf-8 -*-
"""Contrato unificado `economico/contabilidad`.

Une las 4 dimensiones del modelo A+B+C+D:
  A — Actividad (Nivel1..Nivel6)            → economico_actividad
  B — Interlocutor (PersonaFisica/Juridica) → economico_interlocutor
  C — Tipo de documento                     → economico_documento
  D — Cuenta PGC (905 cuentas válidas)      → economico_cuenta_pgc

Declara el dominio pero NO los datos. Los datos viven en Postgres
(pgc_cuenta, pgc_jerarquia, y las tablas que se crearán en Ciclo 3).
"""
from __future__ import annotations

from parsers.contrato_dominio import (
    ContratoDominio,
    VIEW_TYPE_COMPOSITE,
)


def contrato_economico_contabilidad() -> ContratoDominio:
    return ContratoDominio(
        dominio="economico",
        subdominio="contabilidad",
        objetos_internos=[
            "actividad",
            "persona_fisica",
            "persona_juridica",
            "documento_economico",
            "cuenta_pgc",
            "asiento",
            "movimiento",
            "justificacion_interna",
        ],
        evidencias_pertinentes=[
            "factura_emitida",
            "factura_recibida",
            "nomina",
            "extracto_bancario",
            "recibo",
            "contrato",
            "hoja_calculo_obra_ejecutada",
        ],
        pruebas_pertinentes=[
            "documento_con_importe_y_fecha",
            "movimiento_conciliado",
            "justificacion_interna_firmada",
        ],
        hipotesis=[
            (
                "H_CLASIFICACION_CORRECTA",
                "El movimiento está correctamente tipado y su documento asociado cuadra",
            ),
        ],
        mapa_constriccion={
            "DOCUMENTO_NO_CUADRA": {"H_CLASIFICACION_CORRECTA"},
            "IMPORTE_NO_COINCIDE": {"H_CLASIFICACION_CORRECTA"},
            "CONTRAPARTE_NO_IDENTIFICADA": {"H_CLASIFICACION_CORRECTA"},
        },
        competencia={
            "jurisdiccion": "ECONOMICO",
            "competencia": "ENTIDAD",
            "procedimiento": "REGISTRO",
            "forma": "DOCUMENTAL",
        },
        hereda_del_padre=False,
        view_type=VIEW_TYPE_COMPOSITE,
        reglas={
            "cuentas_pgc_total": 905,
            "actividad_niveles": 6,
            "tipos_documento_total": 23,
        },
    )


CONTRATO_ECONOMICO_CONTABILIDAD = contrato_economico_contabilidad()
