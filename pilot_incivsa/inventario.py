"""Inventario en memoria de INCIVSA sin leer ni modificar PostgreSQL."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


RAIZ = Path(__file__).resolve().parent.parent
CSV_IN = RAIZ / "mdb_extraido_InCiv2010" / "0302T.csv"
EMPRESA_HEREDADA = "INCIV_2010"


def analizar_csv() -> dict:
    if not CSV_IN.exists():
        return {"error": "CSV inexistente", "ruta": str(CSV_IN)}

    grupos: dict[tuple[str, str], list[list[str]]] = defaultdict(list)
    filas_validas = 0
    filas_ignoras = 0

    with CSV_IN.open(encoding="latin-1", newline="") as fichero:
        lector = csv.reader(fichero)
        next(lector, None)
        for fila in lector:
            if len(fila) < 13:
                filas_ignoras += 1
                continue
            codigo_asiento = fila[5].strip()
            fecha = fila[6].strip()
            if not codigo_asiento or not fecha:
                filas_ignoras += 1
                continue
            grupos[(codigo_asiento, fecha)].append(fila)
            filas_validas += 1

    asientos_cuadrados = 0
    asientos_descuadrados = 0

    for filas in grupos.values():
        debe = 0
        haber = 0
        for fila in filas:
            try:
                debe += int(round(float(fila[11].strip().replace(",", "")) * 100))
            except (TypeError, ValueError):
                pass
            try:
                haber += int(round(float(fila[12].strip().replace(",", "")) * 100))
            except (TypeError, ValueError):
                pass

        debe = abs(debe)
        haber = abs(haber)
        if debe == haber:
            asientos_cuadrados += 1
        else:
            asientos_descuadrados += 1

    return {
        "empresa_funcional": "INCIVSA",
        "empresa_historica": EMPRESA_HEREDADA,
        "ruta": str(CSV_IN),
        "grupos_brutos": len(grupos),
        "filas_validas": filas_validas,
        "filas_ignoradas": filas_ignoras,
        "grupos_cuadrados_brutos": asientos_cuadrados,
        "grupos_descuadrados_brutos": asientos_descuadrados,
    }
