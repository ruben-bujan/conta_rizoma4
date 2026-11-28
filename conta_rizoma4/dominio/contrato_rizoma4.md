# Contrato conceptual de integración con RIZOMA4

## Regla principal

RIZOMA4 será una integración extraordinaria opcional.

CONTA-RIZOMA4 conservará:

- autonomía funcional;
- modelo ordinario independiente;
- evidencia contable local;
- reconstrucción económica propia;
- decisiones contables locales;
- persistencia ordinaria propia;
- responsabilidad sobre la representación contable.

RIZOMA4 no podrá:

- autorizar contabilidad ordinaria por defecto;
- sustituir hechos por hipótesis;
- modificar asientos sin evento contable;
- borrar interpretaciones;
- imponer una decisión contable;
- convertirse en única fuente de verdad;
- borrar o reemplazar evidencia local.

## Información enviada por CONTA

- identificador estable de hecho;
- identificador de entidad;
- fecha económica;
- fecha de conocimiento;
- estado epistemológico;
- referencias documentales;
- hash de evidencia;
- interpretación adoptada;
- criterios aplicados;
- decisión y autorización resumida;
- representación contable;
- estado de rectificación;
- alerta o incertidumbre;
- versión del modelo.

## Información recibida de RIZOMA4

- identificador de caso;
- hipótesis extraordinaria;
- evidencia adicional;
- fuente externa;
- alerta;
- nivel o clasificación epistémica;
- interpretación alternativa;
- solicitud de revisión;
- fecha de conocimiento;
- responsable de integración;
- versión de modelo extraordinario.

## Responsabilidad

RIZOMA4 podrá:

- proponer hipótesis;
- identificar contradicciones;
- solicitar revisión;
- aportar evidencia extraordinaria;
- analizar integración diferencial.

CONTA deberá:

- validar referencias;
- preservar hechos originales;
- distinguir hipótesis de hechos;
- decidir qué interpretación adopta;
- autorizar efectos contables;
- registrar la integración como evento.

## Separación de identificadores

- Los identificadores RIZOMA4 no sustituyen los de CONTA.
- Los identificadores CONTA no sustituyen los de RIZOMA4.
- Toda relación será un mapeo bidireccional explícito.

## Estados separados

Estados CONTA:

- hecho acreditado;
- representación contable;
- decisión;
- rectificación;
- ejercicio.

Estados RIZOMA4:

- caso;
- hipótesis;
- integración diferencial;
- alerta;
- cuarentena extraordinaria.

Los estados no deben traducirse directamente entre sí.

## Eventos de integración

- `CASO_VINCULADO`;
- `CASO_DESVINCULADO`;
- `HIPOTESIS_RECIBIDA`;
- `ALERTA_RECIBIDA`;
- `EVIDENCIA_EXTRAORDINARIA_RECIBIDA`;
- `REVISION_SOLICITADA`;
- `INTEGRACION_CONFIRMADA`;
- `INTEGRACION_RECHAZADA`.

Cada evento debe registrar:

- fecha;
- objeto CONTA;
- objeto RIZOMA4;
- actor local;
- resultado;
- motivo;
- versión del contrato;
- autenticación de integración.

## Fallback

Si RIZOMA4 no está disponible:

- la contabilidad ordinaria debe seguir operando;
- el caso extraordinario puede quedar pendiente;
- no debe alterarse automáticamente el estado contable;
- debe registrarse la indisponibilidad;
- una revisión posterior debe conservar el evento.

## Seguridad

El contrato debe exigir:

- autenticación Bearer o equivalente;
- identificación de integración;
- mínima exposición de datos;
- trazabilidad;
- verificación criptográfica;
- registro de versión;
- límites de información;
- control de confidencialidad;
- reconciliación posterior.
