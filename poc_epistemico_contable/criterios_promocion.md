# Criterios de promoción de la POC a núcleo

## Funcionalidad obligatoria

- El dominio puede funcionar en memoria sin servicios externos.
- Existe identidad propia para hechos, evidencias, interpretaciones, decisiones y representaciones.
- Los hechos no se confunden con asientos.
- La evidencia conserva fuente, integridad, autenticidad y veracidad como dimensiones separadas.
- Las interpretaciones alternativas se conservan y pueden ser adoptadas o descartadas.
- Las decisiones conservan actor, motivo, evidencia y criterio.
- Las representaciones contables conservan su vínculo con hechos y decisiones.
- Las rectificaciones conservan el objeto original.
- El ledger conserva estado anterior y posterior.
- La reconstrucción puede realizarse por fecha epistémica.
- El hash no se usa como prueba de autenticidad o veracidad.

## Compatibilidad obligatoria

- `Linea` y `Asiento` pueden convertirse desde y hacia la POC.
- Los actos puros pueden ejecutarse sin persistencia.
- Los actos informativos no se representan automáticamente como asientos.
- Las rectificaciones pueden distinguirse de operaciones económicas ordinarias.
- Los módulos heredados permanecen operativos durante la transición.

## Calidad obligatoria

- Las pruebas del vertical slice pasan sin servicios externos.
- Las pruebas de adaptación pasan sin PostgreSQL.
- Las pruebas de catálogo pasan sin importar el paquete heredado.
- Las transiciones inválidas quedan rechazadas.
- Los asientos descuadrados quedan rechazados.
- Las rectificaciones sin origen quedan rechazadas.
- Las decisiones sin interpretación quedan rechazadas.
- Las evidencias sin fuente quedan rechazadas.

## Criterios de salida

Promover únicamente si:

- el modelo demuestra los cinco escenarios conceptuales;
- el ledger puede reconstruirse íntegramente;
- los primeros actos migrados mantienen compatibilidad contable;
- el sistema heredado puede seguir utilizándose sin cambios;
- PostgreSQL puede incorporarse como adaptador posterior;
- Rizoma4 puede incorporarse como integración opcional posterior.

## Criterios de bloqueo

No promover si:

- el núcleo depende de SQL;
- el núcleo importa FastAPI;
- el núcleo exige Rizoma4;
- el hecho sigue siendo un asiento;
- la evidencia automática acredita el hecho;
- los metadatos libres sustituyen relaciones;
- el índice contable sustituye la identidad económica;
- una rectificación elimina el original;
- el estado se modifica sin evento;
- el criterio histórico cambia sin versión;
- el autor se representa sólo por texto libre.
