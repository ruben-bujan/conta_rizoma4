# conta-rizoma4

**Contabilidad doctrinal sobre el PGC español.** Cada asiento se traza
a un párrafo del Plan General de Contabilidad. La forma (el asiento) es
el vehículo de la sustancia (la realidad económica), como dice el PGC
en su párrafo 4 y como rizoma4 formaliza en su regla §6 #37.

Cliente del kernel epistémico rizoma4. conta-rizoma4 sabe que existe
rizoma4. rizoma4 no sabe que existe conta-rizoma4.

## Estado (2026-11-15)

- Actos implementados: **115**
- Tests: **266**
- Grupos: **14**
- Cobertura PGC: **100%** de la taxonomía original
- Commits: 11

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
todos los libros. Resultado: beneficio 1.325 EUR, balance cuadrado.

## Los 115 actos (14 grupos)

| Grupo | Actos | Que cubre |
|---|---|---|
| facturacion | 14 | Facturas emitidas/recibidas, cobros, pagos, nominas |
| facturacion_avanzada | 7 | Simplificadas, autofactura, descuentos, rappel, recargo |
| fiscal | 11 | IVA 303/390, IRPF 111/115/123/180/190/193, IS 200 |
| fiscal_avanzado | 23 | 347/349/369/130/131, IAE/IBI/ITP, sanciones, forales |
| cierre | 3 | Regularizacion, cierre, apertura |
| inmovilizado | 5 | Compra, venta, amortizacion, deterioro, baja |
| inmovilizado_avanzado | 6 | Leasing, permuta, activo venta, actualizacion |
| existencias | 4 | Compra, venta, regularizacion, deterioro |
| existencias_avanzado | 3 | Correccion, deterioro reversible, FIFO |
| societarias | 5 | Constitucion, ampliacion, dividendo, reserva |
| societarias_avanzado | 7 | Autocartera, dividendo a cuenta, aplicacion resultado |
| ajustes | 9 | Subvenciones, periodificaciones, cambio, provisiones |
| ajustes_avanzado | 5 | Desmantelamiento, medioambiental, coberturas |
| operaciones_especiales | 13 | Fusiones, consolidacion, derivados, confirming |

Ver el catalogo completo:

    conta pd-acto listar

## Lo que NO hace

- No presenta cuentas anuales en formato oficial del Registro Mercantil.
- No pre-rellena el modelo 200/303 para AEAT.
- No calcula FIFO/PMP automaticamente (el acto FIFO existe, el calculo no).
- No integra con rizoma4 (puentes pendientes, 2027).
- No consolida grupos automaticamente (el acto de eliminacion existe, el motor no).

## Arquitectura

    conta_rizoma4/
    ├── contratos/          A+B+C+D (declarativo)
    ├── operativo/          hash chain + mapeo + justificacion (POC legacy, deprecated)
    ├── partida_doble/      partida doble real + libros + cuentas anuales
    ├── actos/              115 actos en 14 grupos
    ├── operaciones.py      helper crear_acto_por_codigo
    ├── cli.py              CLI unificado (POC DEPRECATED + partida doble)
    └── cli_pd.py           comandos de partida doble (recomendado)

### Modelo de datos

| Tabla | Que |
|---|---|
| pgc_cuenta | 905 cuentas validas del PGC |
| pgc_texto | 3251 parrafos del PGC legal |
| pgc_jerarquia | 927 filas (Nivel1..Nivel6) |
| asiento_contable | Cabecera del asiento + hash |
| linea_asiento | Lineas con debe/haber (valida SUM(debe)=SUM(haber)) |
| acto_economico | POC legacy (deprecated) |
| justificacion_interna | POC legacy (deprecated) |

## Comandos del CLI

### Partida doble (recomendado)

    conta pd-acto listar [--grupo G]      # 115 actos en 14 grupos
    conta pd-acto crear CODIGO --json '{}' # crear asiento
    conta pd-diario [--desde N --hasta N]  # libro diario
    conta pd-mayor [--cuenta X]            # libro mayor
    conta pd-balance                        # balance de comprobacion
    conta pd-pyg                            # perdidas y ganancias
    conta pd-situacion                      # balance de situacion
    conta pd-verificar [--desde N]          # verificar cadena hash
    conta pd-reset [--yes]                  # limpiar BD

### POC (deprecated, legacy)

    conta sugerir      # [DEPRECATED] Usa pd-acto
    conta justificar   # [DEPRECATED] Usa pd-acto
    conta crear        # [DEPRECATED] Usa pd-acto crear
    conta reclasificar # [DEPRECATED]
    conta listar       # [DEPRECATED] Usa pd-diario
    conta ver          # [DEPRECATED] Usa pd-diario
    conta verificar    # [DEPRECATED] Usa pd-verificar
    conta pendientes   # [DEPRECATED]
    conta reset        # [DEPRECATED] Usa pd-reset

## Tests

    pytest tests/ -q

Esperado: 266 passed.

## Como anadir un acto nuevo

1. Anadir la funcion a conta_rizoma4/actos/<grupo>.py
2. Anadirla al dict ACTOS del modulo
3. El catalogo se actualiza solo (lee los dicts)
4. Anadir un golden test en tests/test_actos_<grupo>.py
5. Commit

## Doctrina

El **PGC parrafo 4** dice: "en la contabilizacion de las operaciones se
atendera a su realidad economica y no solo a su forma juridica".

**Rizoma4 §6 #37** dice: "La forma es el vehiculo de la sustancia. Sin
forma no hay sustancia procesable".

**conta-rizoma4** lo materializa: cada asiento tiene su parrafo del PGC
que lo justifica, su hash encadenado, y su cadena de mando. Si alguien
manipula un acto, conta pd-verificar lo detecta.

Eso es la cadena de custodia doctrinal.

## Proximo (Ciclo 13)

- Usar el sistema con datos reales durante una semana.
- Lo que duela es la especificacion del Ciclo 13.
- Si no duele nada: pausa larga hasta jv-rizoma4 (2027).
