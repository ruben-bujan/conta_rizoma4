# Preflight de migración INCIVSA — 2026-11-25

## Autorización

El usuario autorizó migrar INCIVSA y declaró levantados los bloqueos previos. Esta autorización no altera el CSV ni identifica por sí sola el servidor/instancia destino.

## Origen verificado en memoria

- Archivo: copia de trabajo `mdb_extraido_InCiv2010/0302T.csv`.
- SHA-256: `33dfa4a99d936383ce38b6f6fe5d28f880262f4fc3fadd02af060535da93c504`.
- Grupos fuente: 1.312.
- Filas omitidas por estructura: 0.
- Asientos construidos y cuadrados por el parser decimal estricto: 1.204.
- Grupos sin representación automática: 108, todos por importes con más de dos decimales.
- Los 1.204 asientos construidos cuadran en memoria.
- El código de origen se repite: 1.312 grupos contienen 837 códigos distintos; 269 códigos aparecen en más de una fecha. La identidad de origen es el par código+fecha y no cabe en el importador actual, que sólo acepta empresa+índice único.

No se imprimieron ni copiaron al informe conceptos, terceros, importes individuales ni datos personales. Los 108 grupos permanecen sin clasificación automática; no se redondearon.

## Riesgos del importador existente

`scripts/importar_inciv_2010.py` no se ejecutó. Su `main()` llama a `_limpiar()`, que borra asientos, líneas y documentos de `INCIV_2010`; convierte importes con `float`; puede generar placeholders si se habilita una variable de entorno; y crea índices nuevos desde el máximo existente, por lo que no es idempotente ante reejecución.

## Estado de destino

- Se localizó el contenedor `conta_rizoma4_postgres`; la base `conta_rizoma4` responde a consultas de solo lectura.
- Tiene 6 asientos existentes, ninguno de `INCIV_2010`; aún no tiene `dominio_correspondencia_heredada`.
- Se creó copia lógica previa en `/tmp/conta-rizoma4-pre-incivsa-7306nv4w.dump`, modo 0600, SHA-256 `2c982a4f3dc6ff2c43816795ce0593d6ff816d57622dac330a34c45bbd52c93d`. `pg_restore --list` reconoció el archivo.
- La configuración `CONTA_PG_*`/`CONTA_PG_URL` sigue ausente; el controlador `psycopg` 3.3.9 se instaló en `.venv`. Se requiere acceso al contenedor para conectar.
- La base existente contiene otros datos y no se ha confirmado que sea una instancia desechable. No se aplicó DDL ni se escribió en ninguna base.
- La revisión estática encontró una anotación Python inválida en `scripts/ddl_partida_doble.sql`; se corrigió en el archivo de diseño a `parrafo_pgc_id INTEGER NULL`. Este DDL corregido aún no se ha aplicado.

## Resultado

**Migración no ejecutada; preflight detenido antes de persistencia.** Para continuar hace falta:

1. Un destino PostgreSQL desechable/aislado identificado, con DDL aprobado y conexión configurada en el entorno (no enviar secretos por chat).
2. La clave compuesta código+fecha para las correspondencias; el esquema/adaptador actuales usan un índice numérico y no identifican inequívocamente los 1.312 grupos.
3. Conservar los 108 grupos subcéntimo como `NO_DETERMINADO` (interpretación adoptada de «adelante»); no se redondearon.
4. Una ruta de migración append-only con verificación de reejecución, respaldo/restauración y rollback físico probados. El importador heredado no satisface estas condiciones: además de borrar datos y usar `float`, marca entradas como `APROBADO` y asigna actores declarativos.

## Continuación autorizada

El usuario autorizó después la incorporación contable al proyecto. La migración segura en borrador se completó; los resultados posteriores, el lote y sus verificaciones están en [informe_migracion_2026-11-25.md](informe_migracion_2026-11-25.md). Las observaciones de este preflight describen el estado anterior a la persistencia.
