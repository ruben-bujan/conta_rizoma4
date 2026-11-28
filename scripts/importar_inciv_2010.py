#!/usr/bin/env python3
"""Compatibilidad histórica: delega en el importador INCIVSA seguro.

El flujo antiguo se retiró porque permitía borrar asientos, crear documentos
ficticios y asignar estados/actores de aprobación sin revisión contable.
"""
from __future__ import annotations

import sys

from incorporar_incivsa import main


if __name__ == "__main__":
    raise SystemExit(main())
