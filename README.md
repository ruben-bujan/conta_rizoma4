cat > /home/ruben/MyProyecto/conta-rizoma4/README.md <<'PYEOF'
# conta-rizoma4

**Contabilidad doctrinal sobre el PGC español.** Cada asiento se traza a
un párrafo del Plan General de Contabilidad. La forma (el asiento) es el
vehículo de la sustancia (la realidad económica), como dice el PGC en su
párrafo 4 y como rizoma4 formaliza en su regla §6 #37.

Cliente del kernel epistémico `rizoma4`. `conta-rizoma4` sabe que existe
`rizoma4`. `rizoma4` no sabe que existe `conta-rizoma4`.

## Estado (2026-11-15)

| Ciclo | Contenido | Tests |
|---|---|---|
| 1 | PGC en Postgres: 905 cuentas, 3251 párrafos, 927 jerarquía | 5 |
| 2 | Contratos A+B+C+D (actividad, interlocutor, documento, cuenta) | 15 |
| 3 | Capa operativa: hash chain, mapeo, acto, justificación | 23 |
| 4 | Repositorio con verificación de cadena (detecta tampering) | 10 |
| 5 | Reclasificación del devengo (4308 → 430) | 10 |
| 6 | CLI (8 comandos) | 9 |
| **Total** | | **72** |

## Instalación

```bash
# 1. Dependencia (kernel epistémico)
cd ~/MyProyecto/rizoma4 && pip install -e .

# 2. Este paquete
cd ~/MyProyecto/conta-rizoma4 && pip install -e ".[test]"

# 3. Sembrar el PGC en Postgres (requiere MariaDB con la DB Contabilidad)
export MARIADB_PASSWORD='NuevaRootFuerte_2026'
python scripts/seed_pgc.py

# 4. Aplicar DDL operativo (idempotente)
python scripts/aplicar_ddl_operativo.py