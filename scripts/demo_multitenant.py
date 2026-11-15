#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Demo multi-tenant: 3 empresas + consolidación."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg

from conta_rizoma4.partida_doble import (
    RepositorioAsiento, guardar_asiento,
    balance_situacion, cuenta_pyg,
)
from conta_rizoma4.partida_doble.persistencia import PG_URL
from conta_rizoma4.actos.catalogo import obtener
from conta_rizoma4.operativo.asiento import GENESIS
from conta_rizoma4.consolidacion import (
    consolidar_grupo, guardar_relacion, RelacionGrupo,
)


MATRIZ = "DEMO_MATRIZ"
FILIAL_A = "DEMO_FILIAL_A"
FILIAL_B = "DEMO_FILIAL_B"
EMPRESAS = [MATRIZ, FILIAL_A, FILIAL_B]


def _limpiar():
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            for emp in EMPRESAS:
                cur.execute(
                    "DELETE FROM linea_asiento WHERE empresa_id = %s", (emp,)
                )
                cur.execute(
                    "DELETE FROM asiento_contable WHERE empresa_id = %s", (emp,)
                )
            cur.execute(
                "DELETE FROM relaciones_grupo WHERE matriz_id = %s", (MATRIZ,)
            )
        conn.commit()


def _crear(empresa, codigo, **params):
    repo = RepositorioAsiento(empresa)
    ult = repo.ultimo_indice()
    ult_d = repo.obtener(ult) if ult >= 0 else None
    hp = ult_d["hash"] if ult_d else GENESIS
    _, fn = obtener(codigo)
    acto = fn(indice=ult + 1, hash_previo=hp, **params)
    guardar_asiento(acto, empresa_id=empresa)
    return acto


def _fmt(c):
    s = "-" if c < 0 else ""
    a = abs(c)
    return f"{s}{a // 100}.{a % 100:02d}"


def main():
    _limpiar()
    print("Demo multi-tenant: 3 empresas + consolidación")
    print()

    guardar_relacion(RelacionGrupo(
        matriz_id=MATRIZ, filial_id=FILIAL_A,
        porcentaje=100.0, fecha_inicio=date(2025, 1, 1),
    ))
    guardar_relacion(RelacionGrupo(
        matriz_id=MATRIZ, filial_id=FILIAL_B,
        porcentaje=80.0, fecha_inicio=date(2025, 1, 1),
    ))

    for emp in EMPRESAS:
        _crear(emp, "A_CONSTITUCION_SOCIEDAD",
            fecha=date(2025, 1, 1), capital_centimos=1_000_000,
            concepto=f"Constitución {emp}")
        _crear(emp, "A_FACT_EMIT_SERV_NAC_SIN_RET",
            fecha=date(2025, 3, 15), base_centimos=500_000, iva_pct=21,
            cliente_nif="B11111111", concepto=f"Factura {emp}")
        _crear(emp, "A_FACT_REC_GASTO_NAC",
            fecha=date(2025, 3, 20), base_centimos=200_000, iva_pct=21,
            cuenta_gasto="629", proveedor_nif="B22222222",
            concepto=f"Gasto {emp}")
        _crear(emp, "A_NOMINA_MENSUAL",
            fecha=date(2025, 3, 31), bruto_centimos=300_000,
            irpf_pct=15, ss_trabajador_pct=6.35, ss_empresa_pct=30,
            trabajador_nif="12345678Z", concepto=f"Nómina {emp}")

        repo = RepositorioAsiento(emp)
        bal = balance_situacion(repo)
        pyg = cuenta_pyg(repo)
        print(f"  {emp}: {repo.contar()} asientos, resultado {_fmt(pyg['resultado'])}")

    print()
    print("Consolidando grupo...")
    cons = consolidar_grupo("JV_VECTOR", MATRIZ, date(2025, 12, 31))
    print(f"  Empresas incluidas: {cons.empresas_incluidas}")
    print(f"  Resultado grupo: {_fmt(cons.resultado_grupo)}")
    print(f"  Atribuible matriz: {_fmt(cons.resultado_atribuible_matriz)}")
    print(f"  Atribuible minoritarios: {_fmt(cons.resultado_atribuible_minoritarios)}")
    print(f"  Cuadra: {cons.cuadra}")

    _limpiar()
    print()
    print("Demo completo.")


if __name__ == "__main__":
    main()
