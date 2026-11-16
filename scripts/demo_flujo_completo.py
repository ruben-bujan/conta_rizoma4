#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Demo del flujo completo de conta-rizoma4.

Flujo:
  1. Crear obra
  2. Pedir lease
  3. Crear asiento (factura) con lease
  4. Visar (jefe de obra)
  5. Aprobar (jefe de producción)
  6. Rizomizar (simulando el worker de rizoma4)
  7. Ver el estado final

Uso:
    # Arrancar la API en otra terminal:
    #   uvicorn conta_rizoma4.api.main:app --port 8001
    python scripts/demo_flujo_completo.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx


CONTA_URL = os.environ.get("CONTA_API_URL", "http://localhost:8001")
EMPRESA = "DEMO_FLUJO"
OBRA = "DEMO_OBRA_001"
OPERARIO_AUX = "aux_001"
OPERARIO_VIS = "jefe_obra"
OPERARIO_APR = "jefe_prod"


def _api():
    return httpx.Client(base_url=CONTA_URL, timeout=30.0)


def _limpiar():
    """Borra los datos del demo (via API de reset, si existe; si no, SQL)."""
    import psycopg
    try:
        with psycopg.connect(
            "postgresql://rizoma:rizoma_dev@localhost:5433/conta_rizoma4"
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM linea_asiento WHERE empresa_id = %s", (EMPRESA,)
                )
                cur.execute(
                    "DELETE FROM asiento_contable WHERE empresa_id = %s", (EMPRESA,)
                )
                cur.execute(
                    "DELETE FROM leases WHERE empresa_id = %s", (EMPRESA,)
                )
                cur.execute(
                    "DELETE FROM obras WHERE empresa_id = %s", (EMPRESA,)
                )
            conn.commit()
    except Exception as e:
        print(f"  (no se pudo limpiar: {e})")


def _header(t: str):
    print()
    print("=" * 70)
    print(f"  {t}")
    print("=" * 70)


def main() -> int:
    with _api() as c:
        # Health
        r = c.get("/health")
        if r.status_code != 200:
            print(f"API no disponible en {CONTA_URL}")
            return 1
        print(f"API OK: {r.json()}")

    _header("1. Limpiar datos previos")
    _limpiar()
    print("  ✓ Limpio")

    with _api() as c:
        _header("2. Crear obra")
        r = c.post("/obras", json={
            "obra_id": OBRA,
            "empresa_id": EMPRESA,
            "nombre": "Autovía AII, PPKK 2018-2027",
            "cliente_nif": "MFOM",
            "presupuesto_centimos": 923000000,
        })
        if r.status_code not in (201, 200):
            print(f"  ✗ {r.status_code}: {r.text}")
            return 1
        print(f"  ✓ Obra {OBRA}")

        _header("3. Pedir lease")
        r = c.post("/leases", json={
            "empresa_id": EMPRESA,
            "obra_id": OBRA,
            "tipo": "asiento",
            "operario": OPERARIO_AUX,
            "duracion_min": 60,
        })
        if r.status_code != 201:
            print(f"  ✗ {r.status_code}: {r.text}")
            return 1
        lease = r.json()
        print(f"  ✓ Lease {lease['lease_id'][:8]}... → índice {lease['indice_reservado']}")

        _header("4. Crear asiento (factura emitida) con lease")
        r = c.post("/asientos", json={
            "empresa_id": EMPRESA,
            "codigo_acto": "A_FACT_EMIT_SERV_NAC_SIN_RET",
            "fecha": "2006-09-30",
            "concepto": "Factura MFOM sep-06 (3%)",
            "creado_por": OPERARIO_AUX,
            "lease_id": lease["lease_id"],
            "obra_id": OBRA,
            "parametros": {
                "base_centimos": 46150_00,   # 46.150,00 €
                "iva_pct": 21,
                "cliente_nif": "MFOM",
            },
        })
        if r.status_code != 201:
            print(f"  ✗ {r.status_code}: {r.text}")
            return 1
        asiento = r.json()
        indice = asiento["indice"]
        print(f"  ✓ Asiento #{indice} (BORRADOR)")
        print(f"    Líneas: {len(asiento['lineas'])}")
        for l in asiento["lineas"]:
            if l["debe_centimos"] > 0:
                print(f"      D {l['cuenta_pgc']:>6}  {l['debe_centimos']/100:>10.2f}")
            else:
                print(f"      H {l['cuenta_pgc']:>6}  {l['haber_centimos']/100:>10.2f}")
        print(f"    Hash: {asiento['hash'][:16]}...")

        _header("5. Visar (jefe de obra)")
        r = c.post(
            f"/asientos/{indice}/visar",
            params={"empresa_id": EMPRESA},
            json={"operario_visador": OPERARIO_VIS},
        )
        if r.status_code != 200:
            print(f"  ✗ {r.status_code}: {r.text}")
            return 1
        print(f"  ✓ Estado: {r.json()['estado']}")

        _header("6. Aprobar (jefe de producción)")
        r = c.post(
            f"/asientos/{indice}/aprobar",
            params={"empresa_id": EMPRESA},
            json={"operario_aprobador": OPERARIO_APR},
        )
        if r.status_code != 200:
            print(f"  ✗ {r.status_code}: {r.text}")
            return 1
        print(f"  ✓ Estado: {r.json()['estado']}")

        _header("7. Rizomizar (simulando el worker de rizoma4)")
        # En producción, el worker de rizoma4 haría esta llamada tras
        # evaluar FTOP + CAS + hipótesis. Aquí simulamos que todo OK.
        r = c.post(
            f"/asientos/{indice}/rizomizar",
            params={"empresa_id": EMPRESA},
            json={"ok": True, "alerta": None},
        )
        if r.status_code != 200:
            print(f"  ✗ {r.status_code}: {r.text}")
            return 1
        print(f"  ✓ Estado: {r.json()['estado']}")

        _header("8. Estado final")
        r = c.get(
            "/asientos",
            params={"empresa_id": EMPRESA, "estado": "RIZOMIZADO"},
        )
        if r.status_code != 200:
            print(f"  ✗ {r.status_code}: {r.text}")
            return 1
        asientos_riz = r.json()
        print(f"  Asientos RIZOMIZADOS: {len(asientos_riz)}")
        for a in asientos_riz:
            print(f"    #{a['indice']}  {a['fecha']}  {a['concepto']}")
            print(f"      Hash: {a['hash'][:16]}...")

        _header("9. Verificar cadena")
        r = c.post("/verificar", json={"empresa_id": EMPRESA})
        if r.status_code != 200:
            print(f"  ✗ {r.status_code}: {r.text}")
            return 1
        rep = r.json()
        print(f"  Cadena: {'✓ VÁLIDA' if rep['cadena_valida'] else '✗ ROTA'}")
        print(f"  Asientos: {rep['total']}")

    _header("FIN")
    print("✓ Flujo completo demostrado: lease → crear → visar → aprobar → rizomizar")
    return 0


if __name__ == "__main__":
    sys.exit(main())
