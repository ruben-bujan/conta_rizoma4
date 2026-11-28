# Incorporación de información contable INCIVSA — 2026-11-25

## Resultado

**INCORPORACIÓN COMPLETADA EN BORRADOR.** Los datos se cargaron en la base local `conta_rizoma4`, contenedor `conta_rizoma4_postgres`, como información heredada no acreditada. No se publicaron como asientos aprobados.

## Identidad y trazabilidad

- Empresa funcional: INCIVSA.
- Identificador de origen conservado: `INCIV_2010`.
- Clave de cada grupo fuente: código de asiento + fecha; cada clave se guarda con SHA-256 para su unicidad.
- Lote: `e71f393a5bb4a4d3253de25da73af9984083db7c4c6659900fd7fba6a532e3bf`.
- SHA-256 de la fuente: `33dfa4a99d936383ce38b6f6fe5d28f880262f4fc3fadd02af060535da93c504`.

## Filas incorporadas

- 4.483 filas fuente conservadas en JSONB, agrupadas en 1.312 registros de `incivsa_grupo_origen`.
- 1.204 grupos con líneas parseables y cuadre exacto se reflejan como 1.204 asientos `BORRADOR`, con 3.963 líneas.
- 108 grupos con importes subcéntimo permanecen `NO_DETERMINADO_PRECISION_O_LINEA`; sus filas originales se conservaron y no se redondearon ni se convirtieron en asiento.
- Las propuestas llevan metadatos `estado_epistemologico=NO_DETERMINADO` y `estado_migracion=IMPORTADO_SIN_ACREDITACION_EPISTEMICA`.
- No se crearon actores, documentos, placeholders, interpretaciones ni decisiones.
- Se preservaron los seis asientos de otras empresas que ya había en la base.
- Los listados ordinarios filtran estos lotes pendientes por defecto; la inclusión requiere `incluir_importaciones_pendientes=True`. El listado por estado permite consultar los borradores para su revisión.
- Verificación del filtro en la base: 1.210 asientos totales, 6 asientos previos visibles en listado ordinario y 1.204 borradores INCIVSA excluidos.

## Verificación

- El ensayo inicial ejecutó DDL e inserciones en una transacción y terminó en rollback.
- La importación confirmada se hizo en una sola transacción y es idempotente por SHA-256 de fuente.
- Reejecutar el importador detecta el lote existente y revierte sin duplicar filas.
- Verificación de lectura posterior: 1.312 grupos, 4.483 filas fuente, 1.204 borradores, 3.963 líneas, cero asientos descuadrados, cero errores de cadena, cero documentos y cero actores asociados.
- Se encontró una discrepancia inicial en el hash por serializar hora cuando la columna almacena fecha. Se corrigieron únicamente `hash_previo`/`hash` de los 1.204 borradores, con un evento `CADENA_HASH_NORMALIZADA` append-only que registra la huella anterior y resultante. La verificación posterior confirma cadena completa.
- Pruebas sintéticas, guardas locales, verificación de migración, bloqueo del importador heredado y filtro de lectura: 31 pasaron. No se ejecutaron pruebas que vuelvan a abrir el CSV real.

## Respaldo

Copia lógica previa en `/tmp/conta-rizoma4-pre-incivsa-7306nv4w.dump`, modo `0600`, SHA-256 `2c982a4f3dc6ff2c43816795ce0593d6ff816d57622dac330a34c45bbd52c93d`. El archivo fue reconocido por `pg_restore --list`; no se ensayó una restauración completa.

## Archivos y límites

- `migrations/006_incivsa_importacion.sql`: tablas de lote y grupos de origen con guardas append-only.
- `scripts/incorporar_incivsa.py`: importador sin limpieza, sin placeholders y con ensayo por rollback.
- `pilot_incivsa/constructor_memoria.py`: conversión decimal estricta y conservación de grupos fuente.
- `scripts/importar_inciv_2010.py` no se ejecutó. Se deshabilitó su entrada y sus funciones de limpieza/persistencia porque borraban datos, marcaban asientos aprobados y asignaban actores declarativos. El código se conserva como referencia histórica.

El usuario deberá revisar los borradores antes de aprobarlos o registrarlos contablemente. Los 108 grupos subcéntimo requieren criterio de valoración explícito. La importación no acredita hechos, documentos, identidad de contrapartes ni validez jurídica.
