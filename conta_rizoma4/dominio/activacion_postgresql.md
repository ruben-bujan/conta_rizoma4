# Activación futura de PostgreSQL

## Principio

PostgreSQL será un adaptador de persistencia. No definirá el modelo epistemológico-contable.

## Fase 1. Diseño físico

Crear tablas separadas para:

- entidades contables;
- hechos económicos;
- relaciones entre hechos;
- fuentes;
- evidencias;
- relaciones evidencia-hecho;
- interpretaciones;
- criterios y versiones;
- decisiones;
- autorizaciones;
- representaciones contables;
- rectificaciones;
- eventos;
- correspondencias con asientos heredados;
- instantáneas derivadas.

## Fase 2. Adaptador

Implementar `RepositorioPostgresDominio`, compatible con `RepositorioDominio`.

Debe proporcionar:

- guardar;
- obtener;
- reconstruir;
- transacciones;
- lectura por fecha epistémica;
- verificación de cadena;
- bloqueo append-only;
- migración dual.

## Fase 3. Importación heredada

Importar sin acreditar:

- asientos;
- líneas;
- hashes;
- empresa;
- índice;
- estado workflow;
- documentos asociados;
- metadatos conocidos;
- operadores declarados;
- casos asociados.

Cada asiento importado debe crear una correspondencia heredada.

## Fase 4. Verificación dual

Comparar:

- número de asientos;
- suma debe/haber;
- hashes heredados;
- líneas;
- fechas;
- conceptos;
- estado;
- empresas;
- documentos;
- rectificaciones conocidas;
- correspondencias.

## Fase 5. Activación controlada

- mantener repositorio en memoria activo para pruebas;
- activar lectura PostgreSQL sólo para empresas aprobadas;
- mantener la API heredada funcional;
- registrar una instantánea inicial;
- activar escritura sólo después de verificación completa;
- mantener rollback reversible.

## Bloqueos obligatorios

No activar si:

- existen datos sin correspondencia;
- existe un hash heredado sin explicación;
- existe una rectificación sin origen;
- existe una evidencia sin fuente;
- existe un actor sin identidad verificable;
- existe una representación sin decisión o correspondencia;
- no existe rollback;
- no se han aprobado los cinco escenarios sobre PostgreSQL;
- no existe verificación dual.

## Requisitos antes de activar el adaptador de lectura

Antes de usar PostgreSQL en modo lectura:

- La migración DDL debe haber sido revisada y aprobada.
- No debe existir escritura a través del adaptador.
- Deben validarse todas las sentencias SELECT/WITH.
- Las consultas deben exigir `entidad_id`.
- Los índices deben existir para hechos y eventos.
- Debe existir verificación dual con el repositorio en memoria.
- Debe existir correspondencia para los asientos heredados.
- Los datos heredados sin hecho económico deben permanecer `NO_DETERMINADO`.
- La activación debe ser reversible por empresa.

## Criterios de salida

La activación será válida cuando:

- el repositorio en memoria y PostgreSQL producen la misma reconstrucción;
- las correspondencias cubren todos los asientos heredados;
- los datos heredados no aparecen como hechos acreditados;
- el ledger histórico pasa la verificación;
- las rectificaciones conservan origen;
- las operaciones nuevas generan eventos;
- el sistema puede volver a modo legado.
