# Expediente piloto: INCIVSA / INCIV_2010

## Identificación aprobada para el piloto

- Nombre funcional: INCIVSA.
- Nombre fiscal: `INCIV, _2010`.
- CIF/NIF: `S/80866700-A80866700`.
- Identificador técnico heredado: `INCIV_2010`.
- Grupo histórico: `INCIV`.
- Empresa del importador: `INCIV_2010`.
- Estado: actualmente sometida a actuaciones judiciales y administrativas extraordinarias.

El nombre fiscal y la identificación deben conservarse como datos históricos y jurisdicción
extraordinaria. No deben interpretarse como acreditación automática de hechos económicos,
responsabilidades, legitimidad, ni validez contable.

Todas las operaciones relacionadas deberán registrar el marco extraordinario, la fuente,
la interpretación adoptada y las reservas que correspondan.

## Estado de aprobación

- Empresa piloto aprobada.
- Pendiente: ejecutar migración real.
- Pendiente: confirmar si INCIVSA es nombre comercial o denominación interna.
- Persistencia bloqueada mientras existan actuaciones extraordinarias no revisadas.

## Fuente heredada

- Archivo: `mdb_extraido_InCiv2010/0302T.csv`.
- Filas observadas en el CSV: 4483 en el resumen de extracción.
- Tabla origen: `0302T`.
- Base original: `/home/ruben/MyProyecto/old/InCiv2010.accdb` según resumen.
- Importador existente: `scripts/importar_inciv_2010.py`.

## Riesgos detectados

- El importador ejecuta una limpieza previa con DELETE.
- La limpieza elimina asientos, líneas y documentos del ámbito `INCIV_2010`.
- El script clasifica actos y establece actores declarativos.
- Los placeholders documentales no son prueba documental.
- El CSV contiene importes convertidos desde float por el importador heredado.
- Los grupos de asientos pueden subdividirse por concepto.
- Los registros que no cuadra se omiten.
- El identificador `INCIVSA` no coincide con el identificador heredado comprobado.

## Restricción absoluta

No ejecutar:

- `scripts/importar_inciv_2010.py`;
- migraciones;
- DDL;
- DELETE;
- limpieza de datos;
- generación de placeholders;
- confirmación PostgreSQL;
- activación API;
- activación Rizoma4.

## Objetivo del ensayo

1. Leer una copia aislada del origen.
2. Construir asientos sin persistencia.
3. Clasificar registros válidos, subdivididos y omitidos.
4. Crear correspondencias reversibles.
5. Comparar heredado y nuevo modelo.
6. No acreditar como hechos los asientos importados.
7. Generar un informe de diferencias.
8. Rechazar activación si existe cualquier divergencia crítica.

## Datos que deben preservarse

- índice heredado;
- fecha;
- concepto;
- cuenta;
- debe;
- haber;
- persona o contraparte;
- código del asiento original;
- origen CSV;
- hash;
- estado workflow heredado;
- documentos asociados;
- actores declarativos;
- clasificación económica;
- errores de origen;
- registros omitidos.

## Estado epistemológico inicial

Todos los asientos importados deben comenzar como:

- `NO_DETERMINADO`

Hasta que exista:

- evidencia suficiente;
- interpretación;
- criterio;
- decisión;
- autorización;
- correspondencia económica.

## Criterios de bloqueo

Bloquear si:

- existe discrepancia entre empresa piloto y empresa heredada;
- existe ausencia de correspondencia;
- existe diferencia de índice;
- existe diferencia de hash;
- existe diferencia debe/haber;
- existe diferencia de fecha o concepto;
- existe registro originario omitido sin explicación;
- existe documento placeholder tratado como prueba;
- existe actor sin identidad verificable;
- existe una eliminación o sobrescritura prevista.
