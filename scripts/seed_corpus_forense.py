#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dataset sintético del corpus forense.

6 casos que cubren:
  - U1/V1 (concurso sostenido)
  - U1/V2 (concurso abierto)
  - U1/V3 (punta de lanza = Rubén)
  - U2 (sin concurso + relevante en empresa)
  - U3 (sin concurso + menoscabo pequeño)
  - no_victima (sin buena fe)

Uso:
    python scripts/seed_corpus_forense.py
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from conta_rizoma4.corpus_forense.modelo import (
    Dano, Expediente, Flujo, Sujeto, calcular_dano,
)
from conta_rizoma4.corpus_forense.repositorios import (
    RepositorioSujeto, RepositorioExpediente, RepositorioFlujo,
    RepositorioDano,
)


CASOS = [
    {
        "sujeto_id": "SYN_CONSTR_XYZ",
        "nombre": "Construcciones XYZ SL",
        "tipo": "MIPYME",
        "sector": "construccion",
        "expediente_id": "SYN_EXP_001",
        "via_u1": "V1",
        "estado_concurso": "recaydo",
        "seccion_sexta": False,
        "calificacion": "fortuito",
        "buena_fe_acreditada": True,
        "medio_prueba_buena_fe": "documentos",
        "nivel_vida_antes": 1_000_000_00,
        "nivel_vida_despues": 200_000_00,  # 80% menoscabo
        "importe_debido": 2_500_000_00,
        "fecha_inicio": date(2013, 1, 1),
        "fecha_renuncia": date(2013, 6, 1),
    },
    {
        "sujeto_id": "SYN_OBRAS_ABC",
        "nombre": "Obras Públicas ABC SA",
        "tipo": "MIPYME",
        "sector": "construccion",
        "expediente_id": "SYN_EXP_002",
        "via_u1": "V2",
        "estado_concurso": "presentado",
        "seccion_sexta": False,
        "calificacion": None,
        "buena_fe_acreditada": True,
        "medio_prueba_buena_fe": "testimonio",
        "nivel_vida_antes": 2_000_000_00,
        "nivel_vida_despues": 1_100_000_00,  # 45% menoscabo
        "importe_debido": 5_000_000_00,
        "fecha_inicio": date(2014, 1, 1),
        "fecha_renuncia": date(2014, 6, 1),
    },
    {
        "sujeto_id": "SYN_RUBEN",
        "nombre": "Rubén (punta de lanza)",
        "tipo": "FISICA",
        "sector": "construccion",
        "expediente_id": "SYN_EXP_003",
        "via_u1": "V3",
        "es_punta_de_lanza": True,
        "estado_concurso": "recaydo",
        "seccion_sexta": False,
        "calificacion": "fortuito",
        "buena_fe_acreditada": True,
        "medio_prueba_buena_fe": "combinacion",
        "nivel_vida_antes": 300_000_00,
        "nivel_vida_despues": 0,  # 100% menoscabo (quiebra)
        "quiebra_modo_vida": True,
        "importe_debido": 150_000_00,
        "fecha_inicio": date(2013, 1, 1),
        "fecha_renuncia": date(2013, 6, 1),
    },
    {
        "sujeto_id": "SYN_SUMIN_DEF",
        "nombre": "Suministros DEF SL",
        "tipo": "MIPYME",
        "sector": "suministros",
        "expediente_id": "SYN_EXP_004",
        "via_u1": None,
        "estado_concurso": "ninguno",
        "seccion_sexta": False,
        "buena_fe_acreditada": True,
        "medio_prueba_buena_fe": "documentos",
        "nivel_vida_antes": 500_000_00,
        "nivel_vida_despues": 425_000_00,  # 15% menoscabo (relevante en empresa, no en modo de vida)
        "importe_debido": 800_000_00,
        "fecha_inicio": date(2014, 1, 1),
        "fecha_renuncia": date(2014, 6, 1),
    },
    {
        "sujeto_id": "SYN_SUMIN_GHI",
        "nombre": "Suministros GHI SL",
        "tipo": "MIPYME",
        "sector": "suministros",
        "expediente_id": "SYN_EXP_005",
        "via_u1": None,
        "estado_concurso": "ninguno",
        "seccion_sexta": False,
        "buena_fe_acreditada": True,
        "medio_prueba_buena_fe": "documentos",
        "nivel_vida_antes": 200_000_00,
        "nivel_vida_despues": 180_000_00,  # 10% menoscabo (pequeño)
        "importe_debido": 200_000_00,
        "fecha_inicio": date(2014, 1, 1),
        "fecha_renuncia": date(2014, 6, 1),
    },
    {
        "sujeto_id": "SYN_JUAN_PEREZ",
        "nombre": "Juan Pérez (autónomo)",
        "tipo": "FISICA",
        "sector": "construccion",
        "expediente_id": "SYN_EXP_006",
        "via_u1": None,
        "estado_concurso": "ninguno",
        "seccion_sexta": False,
        "buena_fe_acreditada": False,  # sin buena fe → no víctima
        "medio_prueba_buena_fe": None,
        "nivel_vida_antes": 100_000_00,
        "nivel_vida_despues": 95_000_00,  # 5% menoscabo
        "importe_debido": 50_000_00,
        "fecha_inicio": date(2014, 1, 1),
        "fecha_renuncia": date(2014, 6, 1),
    },
]


def _limpiar():
    import psycopg
    from conta_rizoma4.corpus_forense.repositorios import PG_URL
    with psycopg.connect(PG_URL) as conn:
        with conn.cursor() as cur:
            # Borrar SOLO los datos del seed (SYN_%)
            cur.execute("DELETE FROM danos WHERE expediente_id LIKE 'SYN_%'")
            cur.execute("DELETE FROM flujos WHERE expediente_id LIKE 'SYN_%'")
            cur.execute("DELETE FROM expedientes WHERE expediente_id LIKE 'SYN_%'")
            cur.execute("DELETE FROM sujetos WHERE sujeto_id LIKE 'SYN_%'")
        conn.commit()


def main() -> int:
    _limpiar()
    repo_s = RepositorioSujeto()
    repo_e = RepositorioExpediente()
    repo_f = RepositorioFlujo()
    repo_d = RepositorioDano()

    for c in CASOS:
        # 1. Sujeto
        repo_s.crear(Sujeto(
            sujeto_id=c["sujeto_id"], tipo=c["tipo"],
            nombre=c["nombre"], sector=c["sector"],
        ))

        # 2. Expediente
        pct = 100.0 * (c["nivel_vida_antes"] - c["nivel_vida_despues"]) / c["nivel_vida_antes"]
        exp = Expediente(
            expediente_id=c["expediente_id"],
            sujeto_id=c["sujeto_id"],
            via_u1=c["via_u1"],
            es_punta_de_lanza=c.get("es_punta_de_lanza", False),
            estado_concurso=c["estado_concurso"],
            seccion_sexta=c["seccion_sexta"],
            calificacion=c.get("calificacion"),
            buena_fe_acreditada=c["buena_fe_acreditada"],
            medio_prueba_buena_fe=c["medio_prueba_buena_fe"],
            nivel_vida_antes_centimos=c["nivel_vida_antes"],
            nivel_vida_despues_centimos=c["nivel_vida_despues"],
            porcentaje_menoscabo=pct,
            quiebra_modo_vida=c.get("quiebra_modo_vida", False),
            fecha_inicio=c["fecha_inicio"],
        )
        repo_e.crear(exp)

        # 3. Flujos
        f1 = repo_f.crear(Flujo(
            id=0, expediente_id=c["expediente_id"],
            fecha=c["fecha_inicio"], concepto="Factura impagada",
            importe_centimos=c["importe_debido"], categoria="factura",
        ))
        f2 = repo_f.crear(Flujo(
            id=0, expediente_id=c["expediente_id"],
            fecha=c["fecha_renuncia"], concepto="Renuncia al interés",
            importe_centimos=0, categoria="renuncia_interes",
            hash_previo=f1.hash,
        ))

        # 4. Daño
        d = calcular_dano(exp, [f1, f2], date(2018, 11, 30))
        repo_d.crear(d)

        print(f"  {c['expediente_id']}: {exp.universo} "
              f"(menoscabo {pct:.0f}%, daño {d.dano_total_centimos/100:,.0f} €)")

    print()
    print("Dataset sintético cargado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
