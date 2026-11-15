# conta-rizoma4

Contabilidad doctrinal sobre el PGC español. Cada asiento se traza a un
párrafo del Plan General de Contabilidad. La forma (el asiento) es el
vehículo de la sustancia (la realidad económica), como dice el PGC en su
párrafo 4 y como rizoma4 formaliza en su regla §6 #37.

Cliente del kernel epistémico rizoma4. conta-rizoma4 sabe que existe
rizoma4. rizoma4 no sabe que existe conta-rizoma4.

## Estado (2026-11-15)

- Actos implementados: 115
- Tests: 184
- Grupos: 14
- Cobertura PGC: 100% de la taxonomía original

## Instalación

    cd ~/MyProyecto/rizoma4 && pip install -e .
    cd ~/MyProyecto/conta-rizoma4 && pip install -e '.[test]'
    export MARIADB_PASSWORD='...'
    python scripts/seed_pgc.py
    python scripts/aplicar_ddl_operativo.py
    docker exec -i rizoma4-postgres psql -U rizoma -d conta_rizoma4 < scripts/ddl_partida_doble.sql

## Quick start

    conta pd-acto crear A_FACT_EMIT_SERV_NAC_SIN_RET --json '{"fecha":"2025-04-15","base_centimos":100000,"iva_pct":21,"cliente_nif":"B12345678","concepto":"Factura F-001"}'
    conta pd-diario
    conta pd-mayor
    conta pd-balance
    conta pd-pyg
    conta pd-situacion
    conta pd-verificar

## Demo completo

    python scripts/demo_completo.py

Crea 10 asientos de un caso realista (Taller RBB SL, Q1 2025) y muestra
todos los libros.

## Los 115 actos (14 grupos)

- facturacion (14): facturas, cobros, pagos, nóminas
- facturacion_avanzada (7): simplificadas, autofactura, descuentos
- fiscal (11): IVA, IRPF, IS
- fiscal_avanzado (23): 347, 349, 369, 130, 131, IAE, IBI, ITP, sanciones
- cierre (3): regularización, cierre, apertura
- inmovilizado (5): compra, venta, amortización, deterioro, baja
- inmovilizado_avanzado (6): leasing, permuta, activo venta
- existencias (4): compra, venta, regularización, deterioro
- existencias_avanzado (3): corrección, deterioro reversible, FIFO
- societarias (5): constitución, ampliación, dividendo, reserva
- societarias_avanzado (7): autocartera, dividendo a cuenta, aplicación
- ajustes (9): subvenciones, periodificaciones, provisiones
- ajustes_avanzado (5): desmantelamiento, coberturas, correcciones
- operaciones_especiales (13): fusiones, consolidación, derivados

Ver el catálogo completo:

    conta pd-acto listar

## Lo que NO hace

- No presenta cuentas anuales en formato oficial del Registro Mercantil.
- No pre-rellena el modelo 200/303 para AEAT.
- No calcula FIFO/PMP automáticamente.
- No integra con rizoma4 (puentes pendientes, 2027).
- Presentación simplificada del balance.

## Tests

    pytest tests/ -q

Esperado: 184 passed.

## Doctrina

PGC párrafo 4: "en la contabilización de las operaciones se atenderá a
su realidad económica y no sólo a su forma jurídica".

Rizoma4 §6 #37: "La forma es el vehículo de la sustancia. Sin forma no
hay sustancia procesable".

conta-rizoma4 lo materializa: cada asiento tiene su párrafo del PGC que
lo justifica, su hash encadenado, y su cadena de mando. Si alguien
manipula un acto, conta pd-verificar lo detecta.

Eso es la cadena de custodia doctrinal.
