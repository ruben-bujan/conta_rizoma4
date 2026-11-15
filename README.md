# conta-rizoma4

Contabilidad doctrinal sobre el PGC espanol. Cada asiento se traza a un
parrafo del Plan General de Contabilidad. La forma (el asiento) es el
vehiculo de la sustancia (la realidad economica), como dice el PGC en su
parrafo 4 y como rizoma4 formaliza en su regla 6 #37.

Cliente del kernel epistemico rizoma4. conta-rizoma4 sabe que existe
rizoma4. rizoma4 no sabe que existe conta-rizoma4 (salvo por el cliente
HTTP de la Fase 4a).

## Estado (2026-11-15)

- Actos implementados: 115
- Tests: 303
- Grupos: 14
- Cobertura PGC: 100% de la taxonomia original
- Multi-tenant: si (empresa_id en asientos)
- Consolidacion: grupo clasico (suma, atribuye minoritarios)
- API HTTP: FastAPI (asientos, verificar, empresas)
- Tipos de cambio: BCE automatico + cache + manual

## Instalacion

    cd ~/MyProyecto/rizoma4 && pip install -e .
    cd ~/MyProyecto/conta-rizoma4 && pip install -e '.[test]'
    export MARIADB_PASSWORD='...'
    python scripts/seed_pgc.py
    python scripts/aplicar_ddl_operativo.py
    docker exec -i rizoma4-postgres psql -U rizoma -d conta_rizoma4 < scripts/ddl_partida_doble.sql
    docker exec -i rizoma4-postgres psql -U rizoma -d conta_rizoma4 < scripts/ddl_multi_tenant.sql
    docker exec -i rizoma4-postgres psql -U rizoma -d conta_rizoma4 < scripts/ddl_consolidacion.sql

## Configuracion multi-empresa

config/empresas.yaml (severamente restringido, no versionado):

    version: 1
    moneda_grupo: EUR
    marco_contable_default: PGC_ES
    empresas:
      - empresa_id: matriz_jv
        nombre: JV-VECTOR Matriz SL
        moneda_funcional: EUR
        marco_contable: PGC_ES
        pais: ES
        grupo: JV_VECTOR
        participacion_matriz: 100.0

La config se carga al arrancar. Cambios: editar + reiniciar. No hay
endpoint para editarla.

## Quick start (CLI)

    conta pd-acto crear A_FACT_EMIT_SERV_NAC_SIN_RET --json '{...}'
    conta pd-diario
    conta pd-balance-formateado
    conta pd-verificar

## API HTTP

    uvicorn conta_rizoma4.api.main:app --port 8001

Endpoints:

    GET  /health                        - health check
    GET  /empresas                      - listado de empresas (config)
    GET  /empresas/{empresa_id}         - detalle
    GET  /asientos?empresa_id=...       - listado
    GET  /asientos/{indice}?empresa_id= - obtener
    POST /asientos                      - crear asiento
    DELETE /asientos/{indice}?empresa_id= - borrar
    POST /verificar                     - verificar cadena hash

Docs: http://localhost:8001/docs

## Consolidacion

    python -c 'from datetime import date; from conta_rizoma4.consolidacion import consolidar_grupo; b = consolidar_grupo("JV_VECTOR", "matriz_jv", date(2025, 12, 31)); print(b.resultado_grupo)'

## Demo reproducible

    python scripts/demo_multitenant.py

Crea 3 empresas, 4 asientos en cada una, consolida, muestra balance.

## Los 115 actos (14 grupos)

- facturacion (14): facturas, cobros, pagos, nominas
- facturacion_avanzada (7): simplificadas, autofactura, descuentos
- fiscal (11): IVA, IRPF, IS
- fiscal_avanzado (23): 347, 349, 369, 130, 131, IAE, IBI, ITP
- cierre (3): regularizacion, cierre, apertura
- inmovilizado (5): compra, venta, amortizacion, deterioro, baja
- inmovilizado_avanzado (6): leasing, permuta, activo venta
- existencias (4): compra, venta, regularizacion, deterioro
- existencias_avanzado (3): correccion, deterioro reversible, FIFO
- societarias (5): constitucion, ampliacion, dividendo, reserva
- societarias_avanzado (7): autocartera, dividendo a cuenta
- ajustes (9): subvenciones, periodificaciones, provisiones
- ajustes_avanzado (5): desmantelamiento, coberturas, correcciones
- operaciones_especiales (13): fusiones, consolidacion, derivados

Ver el catalogo: conta pd-acto listar

## Lo que NO hace

- Presentacion oficial de cuentas anuales (Registro Mercantil).
- Pre-rellenado del modelo 200/303 para AEAT.
- FIFO/PMP automatico (el acto FIFO existe, el calculo no).
- Consolidacion multi-PGC (solo PGC_ES cargado).
- Corpus forense (MIPYMEs + personas fisicas, 2027).
- Autenticacion de la API (se anade cuando haya usuarios).

## Tests

    pytest tests/ -q

Esperado: 303 passed.

## Doctrina

PGC parrafo 4: en la contabilizacion de las operaciones se atendera a
su realidad economica y no solo a su forma juridica.

Rizoma4 6 #37: La forma es el vehiculo de la sustancia. Sin forma no
hay sustancia procesable.

conta-rizoma4 lo materializa: cada asiento tiene su parrafo del PGC que
lo justifica, su hash encadenado, y su cadena de mando. Si alguien
manipula un acto, conta pd-verificar lo detecta.
