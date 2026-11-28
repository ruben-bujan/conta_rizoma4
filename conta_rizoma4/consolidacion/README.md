# Consolidación en memoria

`memoria.py` implementa una primera consolidación reproducible sin adaptadores externos. Registra relaciones de participación, balances individuales y eliminaciones en un diario en memoria. Las consultas filtran por fecha de cierre y por fecha de conocimiento (`conocido_a`), por lo que una autorización posterior no altera una reconstrucción anterior.

## Convenciones de esta primera versión

- Los saldos por cuenta usan debe positivo y haber negativo. El cuadre es la suma de los saldos consolidados igual a cero.
- Las relaciones forman una estructura jerárquica con una matriz por filial activa. La participación indirecta se calcula multiplicando porcentajes.
- El resultado atribuible a minoritarios se calcula por participación económica. Esto no determina por sí mismo el tratamiento contable de minoritarios en estados financieros.
- Una eliminación propuesta no afecta los saldos. Sólo una propuesta con evento posterior de autorización se aplica, preservando la versión previa.
- La autorización registra actor e identificador de autorización declarados por el llamante; todavía no valida competencias contra un registro de autorizaciones.
- Esta primera versión no calcula goodwill, diferencias de consolidación, conversión de moneda, homogeneización contable ni eliminaciones automáticas.

## Decisiones pendientes

- Determinar criterios contables y alcance de consolidación aplicables antes de presentar estados financieros como conformes con un marco normativo.
- Definir cómo se acreditan y validan las autorizaciones y quién puede aprobar eliminaciones.
- Definir políticas para cambios de porcentaje, control sin mayoría, participaciones indirectas múltiples y estructuras complejas.
- Definir el contenido documental mínimo y la conciliación bilateral requerida para cada propuesta intragrupo.
- Definir el tratamiento de periodos distintos, monedas distintas, goodwill y ajustes de adquisición.

Estas limitaciones impiden tratar el resultado como presentación consolidada normativa completa; el módulo es funcional para suma, atribución económica y reconstrucción histórica de los datos registrados.
