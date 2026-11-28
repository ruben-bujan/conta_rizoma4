# Cola de espera 2

Trabajo inicialmente aplazado por orden expresa del usuario y ahora incorporado a la fase referida por nueva decisión del usuario (2026-11-26).

1. **Fase 1 — consolidación normativa completa.** Goodwill y diferenciales, homogeneización, moneda, criterios de control/minoritarios y estados consolidados formales.
2. **Fase 6 — inmovilizado y existencias avanzados.** Completar capacidades avanzadas y revisar su tratamiento contable antes de activarlas como flujo formal.

Revisión 2026-11-26:

- **VERIFICADO:** existen módulos heredados `conta_rizoma4/actos/inmovilizado_avanzado.py` y `conta_rizoma4/actos/existencias_avanzado.py` con leasing, permuta, activos para venta, deterioros reversibles, corrección valorativa y regularización FIFO; 57 pruebas de actos avanzados pasaron en esta revisión. En el dominio, `valorar_salida_existencias` admite FIFO y PMP sobre coste histórico (`conta_rizoma4/dominio/casos_uso/activos_existencias.md:7`).
- **PENDIENTE:** nada de lo anterior está activado ni integrado en el núcleo epistémico; la consolidación completa sigue siendo un módulo de memoria sin aprobación normativa. La base de datos debe permanecer intacta.

Estado: **INCORPORADAS A LA FASE REFERIDA** por instrucción del usuario. Se mantiene la nota técnica: hay implementaciones heredadas y pruebas ya verificadas que deben tenerse en cuenta antes de rehacer trabajo; la base de datos debe permanecer intacta hasta el acta correspondiente.
