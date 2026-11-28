# Presentaciones derivadas

`presentar_pgc` construye una vista analítica a partir de saldos por cuenta. Devuelve importes agrupados por epígrafe y mantiene los identificadores de cuenta para trazar cada importe a su origen. Las reglas se pueden sustituir o extender con `ReglaPresentacion`; gana el prefijo más largo.

Si un saldo distinto de cero no encuentra regla, permanece en `cuentas_sin_clasificar` y `cuadra` queda sin determinar (`None`). La función no declara cumplimiento ni produce el formulario de depósito de cuentas anuales.

## Alcance actual

- Balance analítico por activo, patrimonio neto y pasivo.
- Cuenta de pérdidas y ganancias analítica.
- Reglas base por prefijo para cuentas comunes del PGC.
- Totales y control aritmético, condicionado a que no existan saldos sin clasificar.

No se generan todavía los formularios oficiales normal, abreviado o PGC-PYMES, ECPN, EFE, memoria completa, estados consolidados ni soporte electrónico de depósito. La selección del formulario y su correspondencia completa de cuentas requieren identificar el marco y las circunstancias de la entidad y del ejercicio.

## Paquete analítico PGC-PYMES

`presentar_pymes` fija el perfil de trabajo `PGC_PYMES_ANALITICO_V1` y prepara balance y cuenta de pérdidas y ganancias actuales y comparativos si se aportan ambos mayores y se identifica cada ejercicio. Para el ECPN requiere saldo inicial, variaciones explícitas y saldo final en céntimos; calcula la suma y marca si concilia. Conserva la memoria que se le entregue y señala si faltan datos. No infiere movimientos ni completa una memoria, y siempre devuelve `apta_para_deposito=False`.

El PGC-PYMES enumera balance, cuenta de pérdidas y ganancias, estado de cambios en el patrimonio neto (ECPN) y memoria como documentos integrantes; permite incorporar un estado de flujos de efectivo (EFE). El control del ECPN aquí es aritmético: no verifica la suficiencia ni la clasificación normativa de las variaciones. La presentación del dominio no satisface por sí sola las exigencias de formulación y depósito ni el contenido completo de la memoria.

Los modelos PGC-PYMES se regulan por el [Real Decreto 1515/2007](https://www.boe.es/eli/es/rd/2007/11/16/1515). Para el depósito registral, la [Orden JUS/616/2022](https://www.boe.es/eli/es/o/2022/06/30/jus616) y sus modificaciones, incluida la [Resolución de 19 de mayo de 2026](https://www.boe.es/eli/es/res/2026/05/19/%281%29), establecen los modelos aplicables. El formulario concreto debe verificarse según ejercicio y fecha de presentación; este módulo no afirma que su tabla analítica cubra esos modelos.
