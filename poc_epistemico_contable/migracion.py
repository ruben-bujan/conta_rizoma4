"""Plan de migración gradual del catálogo heredado al núcleo nuevo."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MigracionActo:
    codigo: str
    grupo: str
    prioridad: int
    tipo: str
    estrategia: str


PRIMER_PAQUETE = (
    MigracionActo("A_FACT_EMIT_SERV_NAC_SIN_RET", "facturacion", 1, "HECHO_Y_ASIENTO", "MIGRAR_PROGRESIVAMENTE"),
    MigracionActo("A_FACT_EMIT_SERV_NAC_CON_RET", "facturacion", 1, "HECHO_Y_ASIENTO", "MIGRAR_PROGRESIVAMENTE"),
    MigracionActo("A_FACT_REC_GASTO_NAC", "facturacion", 1, "HECHO_Y_ASIENTO", "MIGRAR_PROGRESIVAMENTE"),
    MigracionActo("A_COBRO_CLIENTE_TRANSF", "facturacion", 1, "HECHO_Y_ASIENTO", "MIGRAR_PROGRESIVAMENTE"),
    MigracionActo("A_PAGO_PROVEEDOR_TRANSF", "facturacion", 1, "HECHO_Y_ASIENTO", "MIGRAR_PROGRESIVAMENTE"),
    MigracionActo("A_ANTICIPO_CLIENTE", "facturacion", 1, "HECHO_Y_ASIENTO", "MIGRAR_PROGRESIVAMENTE"),
    MigracionActo("A_FACT_RECT_EMIT", "facturacion", 2, "RECTIFICACION", "MIGRAR_DESPUES_DECISION"),
    MigracionActo("A_FACT_RECT_REC", "facturacion", 2, "RECTIFICACION", "MIGRAR_DESPUES_DECISION"),
    MigracionActo("A_REGULARIZACION_GRUPOS_6_7", "cierre", 3, "CIERRE", "DIFERIR"),
    MigracionActo("A_CIERRE_EJERCICIO", "cierre", 3, "CIERRE", "DIFERIR"),
    MigracionActo("A_APERTURA_EJERCICIO", "cierre", 3, "CIERRE", "DIFERIR"),
)


OBLIGACIONES_DECLARATIVAS = (
    "A_MODELO_347",
    "A_MODELO_349",
    "A_MODELO_369",
    "A_MODELO_720",
    "A_MODELO_721",
    "A_MODELO_714",
)


def listar_primer_paquete() -> tuple[MigracionActo, ...]:
    return PRIMER_PAQUETE


def prioridad(codigo: str) -> int:
    for acto in PRIMER_PAQUETE:
        if acto.codigo == codigo:
            return acto.prioridad
    return 99
