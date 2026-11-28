# Compatibilidad heredada y congelación de API

## Interfaces que se mantienen

- `Asiento` y `Linea` como modelos técnicos de compatibilidad.
- `crear_asiento()` como generador contable provisional.
- funciones puras de `actos/` como generadores por código.
- diario y mayor como consultas derivadas.
- balances y PyG como presentaciones derivadas.
- CLI existente temporalmente.
- API existente temporalmente.
- repositorio PostgreSQL actual temporalmente.
- modelo legacy temporalmente como adaptador.

## Interfaces que no se mantienen como autoridad

- metadatos libres como hecho económico;
- índice como identidad económica;
- nombres de creador como actor autenticado;
- hash como acreditación epistémica;
- estado único como historia completa;
- párrafo PGC obtenido por coincidencia textual como criterio completo;
- acto informativo como asiento contable;
- borrado físico como rectificación;
- JSON arbitrario como relación doctrinal.

## Adaptaciones obligatorias

- `Asiento` → representación técnica;
- `Linea` → partida técnica;
- `ActoEconomico` → posible hecho/interpretación/representación;
- `JustificacionInterna` → hecho devengado o representación pendiente;
- `revertir_asiento` → rectificación tipada;
- `borrar_asiento` → uso prohibido para datos históricos;
- `estado` → estado workflow más evento;
- `operario_*` → actor autenticado y autorización;
- documentos CAS → evidencia con custodia separada;
- relación caso RIZOMA4 → vínculo extraordinario opcional.

## API pública congelada del dominio

El dominio público podrá exportar:

- entidades económicas;
- entidades epistemológicas;
- entidades contables;
- errores;
- puerto de repositorio;
- núcleo;
- repositorio en memoria;
- compatibilidad POC;
- correspondencias de migración;
- integración RIZOMA4 mínima.

Las implementaciones HTTP, SQL y externalización no pertenecen a esta API.

## Política de eliminación

No eliminar código heredado hasta haber demostrado:

- equivalencia funcional;
- migración de datos;
- verificación de pruebas;
- reconstrucción histórica;
- compatibilidad CLI/API;
- reversión segura;
- activación PostgreSQL;
- contrato RIZOMA4.
