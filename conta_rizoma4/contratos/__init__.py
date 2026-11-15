# -*- coding: utf-8 -*-
"""Contratos del módulo conta-rizoma4. Modelo A+B+C+D.

  A — Actividad (Nivel1..Nivel6, 927 filas)
  B — Interlocutor (PersonaFisica / PersonaJuridica)
  C — Tipo de documento (23 tipos)
  D — Cuenta PGC (905 cuentas válidas)
"""

from .economico_actividad import (
    Actividad,
    NIVELES,
    cargar_jerarquia_actividad,
    invalidar_cache_actividad,
)
from .economico_interlocutor import (
    Interlocutor,
    PersonaFisica,
    PersonaJuridica,
    TipoPersona,
)
from .economico_documento import (
    TipoDocumento,
    TIPOS_DOCUMENTO,
)
from .economico_cuenta_pgc import (
    CuentaPGC,
    cargar_cuentas_pgc,
    cargar_todas_las_cuentas_pgc,
    invalidar_cache_cuentas,
)
from .economico_contabilidad import (
    CONTRATO_ECONOMICO_CONTABILIDAD,
    contrato_economico_contabilidad,
)


def registrar_contratos():
    """Registra economico/contabilidad en rizoma4. Idempotente."""
    from parsers.contrato_dominio import registro_contratos
    registro_contratos.registrar(CONTRATO_ECONOMICO_CONTABILIDAD)
    return registro_contratos


__all__ = [
    "Actividad", "NIVELES", "cargar_jerarquia_actividad", "invalidar_cache_actividad",
    "Interlocutor", "PersonaFisica", "PersonaJuridica", "TipoPersona",
    "TipoDocumento", "TIPOS_DOCUMENTO",
    "CuentaPGC", "cargar_cuentas_pgc", "cargar_todas_las_cuentas_pgc",
    "invalidar_cache_cuentas",
    "CONTRATO_ECONOMICO_CONTABILIDAD", "contrato_economico_contabilidad",
    "registrar_contratos",
]
