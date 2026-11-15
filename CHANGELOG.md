
**`/home/ruben/MyProyecto/conta-rizoma4/CHANGELOG.md`**:

```markdown
# CHANGELOG — conta-rizoma4

## v0.3.0 (2026-11-15) — Ciclo 3: capa operativa

**Qué:** capa operativa completa sobre el PGC real.

- `operativo/asiento.py` — primitivas hash chain (GENESIS, calcular_huella, calcular_hash).
- `operativo/parrafo_pgc.py` — búsqueda del párrafo del PGC que justifica una cuenta.
- `operativo/mapeo_abcd.py` — sugeridor A+B+C→D con cascada de reglas (1.0/0.8/0.6/0.2).
- `operativo/acto_economico.py` — asiento con hash encadenado + cadena de mando.
- `operativo/justificacion_interna.py` — obra ejecutada pendiente de facturar.
- `scripts/ddl_operativo.sql` + `scripts/aplicar_ddl_operativo.py` — tablas Postgres.
- 23 tests nuevos (asiento, acto, mapeo, justificación).
- 1 test e2e de cadena completa.

**Por qué:** el PGC solo (contratos) no basta. Hace falta la capa que
materializa el acto: qué cuenta, qué importe, quién lo crea, qué hash,
qué párrafo lo justifica.

**Tests:** 43 passed + 1 e2e = 44.

## v0.2.0 (2026-11-15) — Ciclo 2: contratos A+B+C+D

**Qué:** contratos del modelo de dimensiones.

- A: `economico_actividad.py` (Nivel1..Nivel6, 927 filas de Postgres).
- B: `economico_interlocutor.py` (PersonaFisica / PersonaJuridica).
- C: `economico_documento.py` (23 tipos).
- D: `economico_cuenta_pgc.py` (905 cuentas válidas; filtra el header "23. INMOVILIZACIONES..." que MariaDB guardó como fila).
- Contrato unificado `economico/contabilidad` (importa de `parsers.contrato_dominio` de rizoma4).

**Por qué:** A+B+C→D es el modelo de dimensiones del PGC. Cada asiento
se clasifica por las 4 dimensiones. D (cuenta PGC) es la que da la
justificación doctrinal.

**Tests:** 15 passed.

## v0.1.0 (2026-11-15) — Ciclo 1: PGC en Postgres

**Qué:** seed del PGC completo desde MariaDB a Postgres.

- 906 cuentas (905 válidas tras filtrar 1 header).
- 3251 párrafos del PGC legal.
- 927 filas de jerarquía (Nivel1..Nivel6).
- `scripts/seed_pgc.py` (idempotente, lee MariaDB, escribe Postgres).

**Por qué:** el PGC es el corpus doctrinal. Sin él, conta-rizoma4 no
tiene nada que justificar. Es el cimiento de todo lo demás.

**Tests:** 5 passed.
## v0.7.0 (2026-11-15) — Ciclo 7: Partida doble real

**Qué:** `asiento_contable` + `linea_asiento` con validación de cuadre.

- `partida_doble/modelo.py` — Linea, Asiento, validación (debe>0 XOR haber>0).
- `partida_doble/creacion.py` — crear_asiento con validación SUM(debe)=SUM(haber).
- `partida_doble/persistencia.py` — guardar_asiento, borrar_asiento.
- `partida_doble/repositorio.py` — RepositorioAsiento + verificar_cadena.
- `scripts/ddl_partida_doble.sql` — tablas + vista `v_asiento_cuadre`.
- `docs/taxonomia_actos_economicos.md` — ~100 actos del PGC completo.
- 13 tests nuevos.

**Por qué:** el POC (v0.6.0) tenía actos con una cuenta principal y contrapartida opcional. No era partida doble: un acto con `cuenta_pgc=705, importe=1210` sin contrapartida era válido, lo que en contabilidad real sería un asiento que no cuadra. La partida doble es el cimiento de todo lo demás (libro diario, mayor, balance, PyG, cuentas anuales).

**Ficheros:** 5 ficheros nuevos en `conta_rizoma4/partida_doble/`, 1 DDL, 1 test, 1 doc.

**Tests:** 13 nuevos. Total: 85.

**Cierra:** Ciclo 7. Base para los Ciclos 8-20 (IVA, cierre, retenciones, inmovilizado, etc.).

---
