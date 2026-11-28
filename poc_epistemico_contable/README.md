# POC epistemológica-contable

## Propósito

Probar el núcleo nuevo sin PostgreSQL, FastAPI, Rizoma4, JWT, CAS o persistencia.

## No forma parte del sistema heredado

Esta POC conserva compatibilidad por adaptadores, pero no importa su persistencia ni modifica sus datos.

## Componentes

- `modelo.py`: entidades y estados mínimos.
- `nucleo.py`: operaciones, ledger y reconstrucción en memoria.
- `adaptadores.py`: conversión a `Asiento` y `Linea` actuales.
- `catalogo.py`: lectura estática del catálogo heredado.
- `migracion.py`: prioridad de migración de actos.
- `test_*.py`: pruebas ejecutables sin infraestructura.

## Ejecución

No requiere pytest:

```text
/bin/python - <<'PY'
from poc_epistemico_contable.test_integracion import (
    test_paquete_migracion_no_superpone_catalogo_legacy,
    test_factura_y_cobro_se_representan_en_memoria,
    test_reconstruccion_y_catalogo_pueden_coexistir,
)

for prueba in (
    test_paquete_migracion_no_superpone_catalogo_legacy,
    test_factura_y_cobro_se_representan_en_memoria,
    test_reconstruccion_y_catalogo_pueden_coexistir,
):
    prueba()
    print(f"PASS {prueba.__name__}")
PY
```

## Criterio de promoción

Promover la POC a núcleo sólo si:

- no requiere infraestructura externa;
- conserva historia epistemológica;
- distingue hechos y representaciones;
- conserva interpretaciones alternativas;
- rectifica sin destruir evidencia;
- reconstruye por fecha epistémica;
- puede adaptarse a los modelos contables existentes;
- puede migrarse progresivamente sin desactivar el sistema heredado.
