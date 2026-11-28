# Informe de no activación — INCIVSA / INCIV_2010

## Estado

**NO ACTIVADO PARA PERSISTENCIA POSTGRESQL.**

Esta decisión se mantiene aunque la extracción CSV produzca asientos cuadres en memoria.

## Identificación

- Nombre funcional: INCIVSA.
- Nombre fiscal: `INCIV, _2010`.
- CIF/NIF: `S/80866700-A80866700`.
- Identificador técnico heredado: `INCIV_2010`.
- Estado extraordinario: actuaciones judiciales y administrativas extraordinarias.

## Resultado del ensayo aislado

- 1312 grupos brutos.
- 4483 filas válidas.
- 1312 asientos cuadres construidos.
- 0 registros omitidos por el inventario.
- 0 errores de fecha observados en el constructor.
- 0 grupos inicialmente descuadrados.
- 0 subdivisiones.
- 0 placeholders generados.
- 0 operaciones PostgreSQL ejecutadas.
- 0 datos modificados o eliminados.

## Bloqueos vigentes

Se bloquea cualquier persistencia, activación o migración mientras:

- las actuaciones extraordinarias no estén revisadas;
- no exista autorización formal específica;
- no exista correspondencia humana de identidades;
- no exista verificación dual completa;
- no exista un entorno aislado;
- no exista verificación de rollback;
- no exista revisión de evidencias;
- no exista criterio doctrinal aplicable;
- no exista decisión contable aprobada;
- no exista responsabilidad profesional definida;
- no existan actores con identidad verificable;
- no exista control de datos sensibles;
- no exista una ventana de activación reversible.

## Riesgos identificados

### Histórico

- El importador existente ejecuta `_limpiar()` y DELETE.
- Puede eliminar asientos, líneas y documentos del ámbito heredado.
- Los datos históricos pueden quedar sustituidos.

### Documental

- Los placeholders no son prueba documental.
- El CSV no acredita por sí solo hechos económicos reales.
- Existen terceros y conceptos que requieren interpretación.

### Jurídico extraordinario

- La identidad está vinculada a actuaciones judiciales y administrativas extraordinarias.
- Las representaciones pueden tener efectos procesales.
- No debe presumirse la legitimidad o validez de una operación por su cuadre.
- Cada interpretación debe conservar reserva y procedencia.

### Técnico

- Importación desde float puede afectar a precisión monetaria.
- La división de asientos por concepto puede crear representaciones nuevas.
- El identificador `INCIVSA` y `INCIV_2010` deben mantenerse separados.
- El nombre fiscal no puede utilizarse como clave primaria heredada sin aprobación.

## Evidencias necesarias para una nueva solicitud

Antes de solicitar activación real:

- copia exacta de la base PostgreSQL actual;
- copia exacta del CSV;
- hash SHA-256 del CSV;
- hash de la base o instantánea;
- informe de correspondencias;
- informe de diferencias;
- informe de registros omitidos;
- identificación del responsable de importación;
- identificación del responsable jurídico;
- identificación del responsable contable;
- matriz de autorizaciones;
- plan de rollback;
- prueba de restauración;
- aprobación formal del entorno aislado;
- revisión de datos personales;
- resolución sobre documentos reales;
- resolución sobre actuaciones extraordinarias.

## Condición de activación

La activación sólo podrá solicitarse si:

1. `INCIVSA` y `INCIV_2010` están formalmente vinculados.
2. La identificación fiscal está confirmada.
3. Las actuaciones extraordinarias han sido revisadas por autoridad competente.
4. La migración es reversible.
5. La verificación dual es completa.
6. Los documentos son reales o están expresamente excluidos.
7. El responsable contable autoriza la representación.
8. El responsable jurídico autoriza el tratamiento extraordinario.
9. El responsable técnico autoriza el rollback.
10. PostgreSQL permanece como adaptador y no como autoridad epistemológica.

## Decisión actual

**NO ACTIVAR.**

La continuidad segura corresponde a:

- ensayo aislado;
- análisis histórico;
- revisión jurídica y contable;
- correspondencia asistida;
- verificación dual;
- activación posterior aprobada.

## Actualización técnica — 2026-11-25

- Se endureció el constructor aislado: los importes se convierten con decimal exacto; fracciones inferiores a un céntimo, valores no finitos y líneas inválidas quedan clasificadas y no producen asientos.
- Se añadieron pruebas con CSV sintético y se ejecutaron junto a las guardas de persistencia: 8 pruebas pasaron.
- El CSV real no se abrió ni se reanalizó en esta iteración. Las cifras del ensayo anterior reproducidas arriba no se han vuelto a verificar.
- PostgreSQL, DDL, placeholders, datos heredados y servicios no se tocaron. La decisión vigente permanece **NO ACTIVAR**.

## Actualización posterior: incorporación autorizada

El usuario autorizó posteriormente incorporar la información contable de INCIVSA al proyecto. Se completó una carga append-only en borrador; no equivale a aprobación contable ni activa la empresa para contabilización ordinaria. Véase [informe_migracion_2026-11-25.md](informe_migracion_2026-11-25.md).
