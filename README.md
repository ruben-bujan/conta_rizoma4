# conta-rizoma4

Contabilidad doctrinal sobre el PGC español. Cada asiento se traza a
un párrafo del Plan General de Contabilidad. La forma (el asiento) es
el vehículo de la sustancia (la realidad económica).

Cliente del kernel epistémico rizoma4. conta-rizoma4 sabe que existe
rizoma4. rizoma4 consume la API de conta (Fase 4a).

## Estado (2026-11-16)

- Actos: 115
- Tests: 316
- Grupos PGC: 14
- Cobertura: 100%
- Multi-tenant: si (empresa_id)
- Consolidación: grupo clásico
- API HTTP: FastAPI
- Custodia: obras, operarios, leases, documentos (Fase 4b)
- Flujo end-to-end: crear → visar → aprobar → rizomizar (Fase 4c)
- Worker de rizomización: en rizoma4

## Instalación

    cd ~/MyProyecto/rizoma4 && pip install -e .
    cd ~/MyProyecto/conta-rizoma4 && pip install -e '.[test]'
    export MARIADB_PASSWORD='...'
    python scripts/seed_pgc.py
    python scripts/aplicar_ddl_operativo.py
    docker exec -i rizoma4-postgres psql -U rizoma -d conta_rizoma4 < scripts/ddl_partida_doble.sql
    docker exec -i rizoma4-postgres psql -U rizoma -d conta_rizoma4 < scripts/ddl_multi_tenant.sql
    docker exec -i rizoma4-postgres psql -U rizoma -d conta_rizoma4 < scripts/ddl_consolidacion.sql
    docker exec -i rizoma4-postgres psql -U rizoma -d conta_rizoma4 < scripts/ddl_custodia.sql

## El flujo real (Fase 4)

    1. Operario pide lease       → POST /leases
    2. Operario crea asiento     → POST /asientos (con lease)      → BORRADOR
    3. Jefe de obra visa         → POST /asientos/{id}/visar       → VISADO
    4. Jefe de producción aprueba→ POST /asientos/{id}/aprobar     → APROBADO
    5. Worker de rizoma4         → POST /asientos/{id}/rizomizar   → RIZOMIZADO
                                   o EN_CUARENTENA

## Demo del flujo completo

    # Terminal A
    uvicorn conta_rizoma4.api.main:app --port 8001

    # Terminal B
    python scripts/demo_flujo_completo.py

Hace los 5 pasos, muestra el estado final y verifica la cadena.

## API HTTP

    uvicorn conta_rizoma4.api.main:app --port 8001

Endpoints:

    GET  /health
    GET  /empresas
    GET  /empresas/{empresa_id}

    POST /obras
    GET  /obras
    GET  /obras/{obra_id}

    POST /operarios
    GET  /operarios
    GET  /operarios/{operario_id}

    POST /leases
    GET  /leases/{lease_id}
    POST /leases/{lease_id}/renovar
    POST /leases/{lease_id}/cancelar

    POST /documentos (sube a CAS de rizoma4)
    GET  /documentos/{hash_cas}

    GET  /asientos?empresa_id=X&estado=Y
    GET  /asientos/{indice}?empresa_id=X
    POST /asientos (con lease_id, obra_id, documento_ref)
    DELETE /asientos/{indice}?empresa_id=X

    POST /asientos/{indice}/visar?empresa_id=X
    POST /asientos/{indice}/aprobar?empresa_id=X
    POST /asientos/{indice}/rizomizar?empresa_id=X

    POST /verificar

Docs: http://localhost:8001/docs

## Los 5 estados del asiento

| Estado | Qué significa | Quién lo pone |
|---|---|---|
| BORRADOR | Creado por operario de obra | POST /asientos |
| VISADO | Visado por jefe de obra | POST /asientos/{id}/visar |
| APROBADO | Aprobado por jefe de producción | POST /asientos/{id}/aprobar |
| RIZOMIZADO | Validado por rizoma4 (sin alertas) | Worker de rizoma4 |
| EN_CUARENTENA | rizoma4 ha lanzado una alerta | Worker de rizoma4 |

## Leases (reserva de índices)

    POST /leases {empresa_id, obra_id, operario, duracion_min}
    → {lease_id, indice_reservado, expira_en}

    POST /asientos {empresa_id, lease_id, indice_reservado, ...}

Si el lease expira, el asiento no se puede crear.

## Consolidación

    python -c 'from datetime import date; from conta_rizoma4.consolidacion import consolidar_grupo; b = consolidar_grupo("JV_VECTOR", "matriz_jv", date(2025, 12, 31)); print(b.resultado_grupo)'

## Los 115 actos (14 grupos)

- facturacion (14): facturas, cobros, pagos, nóminas
- facturacion_avanzada (7): simplificadas, autofactura, descuentos
- fiscal (11): IVA, IRPF, IS
- fiscal_avanzado (23): 347, 349, 369, 130, 131, IAE, IBI, ITP
- cierre (3): regularización, cierre, apertura
- inmovilizado (5): compra, venta, amortización, deterioro, baja
- inmovilizado_avanzado (6): leasing, permuta, activo venta
- existencias (4): compra, venta, regularización, deterioro
- existencias_avanzado (3): corrección, deterioro reversible, FIFO
- societarias (5): constitución, ampliación, dividendo, reserva
- societarias_avanzado (7): autocartera, dividendo a cuenta
- ajustes (9): subvenciones, periodificaciones, provisiones
- ajustes_avanzado (5): desmantelamiento, coberturas, correcciones
- operaciones_especiales (13): fusiones, consolidación, derivados

Ver catálogo: conta pd-acto listar

## Lo que NO hace

- Frontend (PWA) para el operario. Se construye en Fase 4d.
- FTOP + CAS + hipótesis en el worker (simulado como "ok=True" en el demo).
- Presentación oficial de cuentas anuales (Registro Mercantil).
- Modelos 200/303 con formato AEAT.
- FIFO/PMP automático.
- Consolidación multi-PGC (solo PGC_ES cargado).
- Corpus forense (MIPYMEs + personas físicas sucesoras, 2027).

## Arquitectura

    conta_rizoma4/
    ├── contratos/          A+B+C+D (declarativo)
    ├── operativo/          hash chain + mapeo (POC legacy, deprecated)
    ├── partida_doble/      partida doble real + libros
    ├── actos/              115 actos en 14 grupos
    ├── custodia/           obras, operarios, leases, documentos
    ├── consolidacion/      grupo clásico
    ├── config/             empresas.yaml + tipos de cambio BCE
    ├── api/                FastAPI
    │   └── routers/        asientos, empresas, verificar, leases,
    │                       obras, operarios, documentos
    ├── operaciones.py      helper crear_acto_por_codigo
    ├── cli.py              CLI unificado (POC + partida doble)
    └── cli_pd.py           comandos de partida doble

## Tests

    pytest tests/ -q

Esperado: 316 passed.

## Doctrina

PGC párrafo 4: en la contabilización de las operaciones se atenderá a
su realidad económica y no sólo a su forma jurídica.

Rizoma4 §6 #37: La forma es el vehículo de la sustancia. Sin forma no
hay sustancia procesable.

conta-rizoma4 lo materializa: cada asiento tiene su párrafo del PGC que
lo justifica, su hash encadenado, y su cadena de mando. Si alguien
manipula un acto, conta pd-verificar lo detecta.

La cadena de custodia (obras, operarios, leases, estados) usa lo que
rizoma4 ya tiene (CAS, ledger, PAdES, TSA, Merkle).

## Configuración (JSON segmentado)

Copia `config/conta_config.json.example` a `config/conta_config.json` y ajusta
los bloques `admin` (infra, credenciales, JWT, integración RIZOMA4) y `user`
(runtime cliente). El visado del superior controla cambios sensibles
(`visado.requiere_aprobacion_superior`).
