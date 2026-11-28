# conta-rizoma4

Contabilidad e investigación económica con adaptación al PGC español.
Un asiento puede vincularse a un párrafo PGC cuando esa referencia se
proporciona y valida explícitamente; el código no la presume por grupo de cuenta.

Cliente del kernel epistémico rizoma4. conta-rizoma4 sabe que existe
rizoma4. rizoma4 consume la API de conta (Fase 4a).

## Estado (2026-11-26)

- El núcleo epistemológico y varios casos de uso contables funcionan en memoria; la promoción sigue parcial. El núcleo ya registra eventos con hashes encadenados, reconstruye los tipos de proyección de autoridad y aplica la matriz aprobada en decisiones, representaciones, asientos, rectificaciones, cierres y reaperturas (`conta_rizoma4/dominio/README.md`, `gobernanza/matriz_competencias.md`). La API expone `actor_id` y mapea sus roles a `Actor` de dominio (`conta_rizoma4/api/deps.py`).
- La API heredada usa Bearer/JWT y controles por rol/empresa, pero no está habilitada para producción; ya mapea la identidad autenticada a `Actor` del dominio y consulta `dominio_evento` para las delegaciones en asientos. CORS usa lista explícita y el corpus forense queda restringido a administradores.
- La API completa requiere instalar el checkout local de `rizoma4` indicado abajo y configurar PostgreSQL para las operaciones que lo usan. Instalación limpia y despliegue siguen sin verificar.
- Las fases 2, 3, 4, 5 y 7 se han abordado y tienen implementaciones parciales verificadas, pero mantienen brechas funcionales y de validación registradas en `PLAN_CIERRE_BRECHAS.md` y `COLA_ESPERA.md`.
- La consolidación normativa completa sigue aplazada en `COLA_ESPERA_2.md`; las capacidades avanzadas de inmovilizado/existencias existen en el código heredado y tienen 57 pruebas que pasan, pero no están activadas ni integradas en el núcleo.
- No hay una cifra de cobertura integral acreditada: la suite completa en este entorno terminó con 47 fallos y 91 errores. Las suites focales de dominio (138) y actos avanzados (57) sí pasaron; ejecuta las relevantes para el alcance que vayas a modificar.

## Instalación

    cd ~/MyProyecto/rizoma4 && pip install -e .
    cd ~/MyProyecto/conta-rizoma4 && pip install -e '.[test]'
    export MARIADB_PASSWORD='...'
    python scripts/seed_pgc.py
    python scripts/aplicar_ddl_operativo.py
    docker exec -i rizoma4-postgres psql -U rizoma -d conta_rizoma4 < scripts/ddl_partida_doble.sql
    docker exec -i rizoma4-postgres psql -U rizoma -d conta_rizoma4 < scripts/ddl_multi_tenant.sql
    docker exec -i rizoma4-postgres psql -U rizoma -d conta_rizoma4 < scripts/ddl_consolidacion.sql
    docker exec -i rizoma4-postgres psql -U rizoma -d conta_rizoma4 < scripts/ddl_custodia.sql
    docker exec -i rizoma4-postgres psql -U rizoma -d conta_rizoma4 < scripts/ddl_casos_rizoma4.sql

## El flujo real (Fase 4)

1. Administrador reserva lease para un operario → POST /leases
2. El usuario autenticado asociado a ese operario crea el asiento → POST /asientos → BORRADOR
3. Jefe de obra visa         → POST /asientos/{id}/visar       → VISADO
4. Jefe de producción aprueba→ POST /asientos/{id}/aprobar     → APROBADO
5. Administrador registra el resultado autorizado de rizomización → POST /asientos/{id}/rizomizar → RIZOMIZADO
                               or EN_CUARENTENA

No hay actualmente una demo HTTP end-to-end compatible con los roles y
permisos vigentes. No uses las demos heredadas como procedimiento de puesta
en marcha sobre una base con datos reales.

## API HTTP

    uvicorn conta_rizoma4.api.main:app --port 8001

Endpoints:

    GET  /health
    GET  /empresas
    GET  /empresas/{empresa_id}
    GET  /empresas/{empresa_id}/casos-rizoma4/disponibles (admin)
    GET  /empresas/{empresa_id}/casos-rizoma4
    POST /empresas/{empresa_id}/casos-rizoma4 (admin)
    DELETE /empresas/{empresa_id}/casos-rizoma4/{caso_id} (admin)

    POST /obras (admin)
    GET  /obras
    GET  /obras/{obra_id}

    POST /operarios (admin)
    GET  /operarios
    GET  /operarios/{operario_id}

    POST /leases (admin; operario y obra deben pertenecer a su empresa)
    GET  /leases/{lease_id}
    POST /leases/{lease_id}/renovar (admin)
    POST /leases/{lease_id}/cancelar (admin)

    POST /documentos (sube a CAS de rizoma4)
    # No hay endpoint HTTP de lectura de documentos en esta API.

    GET  /asientos?empresa_id=X&estado=Y
    GET  /asientos/{indice}?empresa_id=X
    POST /asientos (admin/aux_obra; con caso_id obligatorio, lease_id, obra_id, documento_ref)
    # No existe borrado físico de asientos; corregir mediante reversión.

    POST /asientos/{indice}/visar?empresa_id=X (admin/visador)
    POST /asientos/{indice}/aprobar?empresa_id=X (admin/aprobador)
    POST /asientos/{indice}/rizomizar?empresa_id=X (admin)

    POST /verificar

    POST /auth/login
    POST /auth/registro (admin; empresa heredada de la sesión)
    GET  /auth/me
    GET/POST /corpus/* (solo admin hasta contar con aislamiento por empresa)

Docs: http://localhost:8001/docs

## Los 5 estados del asiento

| Estado | Qué significa | Quién lo pone |
|---|---|---|
| BORRADOR | Creado por operario de obra | POST /asientos |
| VISADO | Visado por jefe de obra | POST /asientos/{id}/visar |
| APROBADO | Aprobado por jefe de producción | POST /asientos/{id}/aprobar |
| RIZOMIZADO | Validado por rizoma4 (sin alertas) | Worker de rizoma4 |
| EN_CUARENTENA | rizoma4 ha lanzado una alerta | Worker de rizoma4 |

## Asociación con casos RIZOMA4 (Bloque 1)

La relación empresa-caso se administra desde la API de CONTA y admite varios casos por empresa.
Un administrador consulta `GET /empresas/{empresa_id}/casos-rizoma4/disponibles` y asocia
los casos mediante `POST /empresas/{empresa_id}/casos-rizoma4`; la desasociación es lógica
(`DELETE`) y conserva el historial. La credencial de integración para consultar RIZOMA4
se configura mediante `RIZOMA4_API_TOKEN` cuando RIZOMA4 exige autenticación.

Configura `CONTA_API_CORS_ORIGINS` con los orígenes concretos de clientes externos.
Sin esa variable no se habilita CORS entre orígenes. Consulta [AUTH.md](conta_rizoma4/api/AUTH.md)
para el secreto JWT y el alta inicial de administrador.

Al crear un asiento, `caso_id` es obligatorio y debe estar asociado y activo para la empresa.
El identificador se incluye en los metadatos cubiertos por el hash del asiento y se almacena
también en una columna propia. Desactivar una asociación no altera los asientos históricos.

## Leases (reserva de índices)

    POST /leases {empresa_id, obra_id, operario, duracion_min}
    → {lease_id, indice_reservado, expira_en}

    POST /asientos {empresa_id, caso_id, lease_id, indice_reservado, ...}

Si el lease expira, el asiento no se puede crear.

## Consolidación

    python -c 'from datetime import date; from conta_rizoma4.consolidacion import consolidar_grupo; b = consolidar_grupo("JV_VECTOR", "matriz_jv", date(2025, 12, 31)); print(b.resultado_grupo)'

## Los 115 actos (14 grupos)

- facturacion (14): facturas, cobros, pagos, nóminas
- facturacion_avanzada (7): simplificadas, autofactura, descuentos
- fiscal (11): IVA, IRPF, IS
- fiscal_avanzado (23): 347, 349, 369, 130, 131, IAE, IBI, ITP
- cierre (3): regularización, cierre, apertura
- inmovilizado (5): compra, venta, amortización, deterioro, baja
- inmovilizado_avanzado (6): leasing, permuta, activo venta
- existencias (4): compra, venta, regularización, deterioro
- existencias_avanzado (3): corrección, deterioro reversible, FIFO
- societarias (5): constitución, ampliación, dividendo, reserva
- societarias_avanzado (7): autocartera, dividendo a cuenta
- ajustes (9): subvenciones, periodificaciones, provisiones
- ajustes_avanzado (5): desmantelamiento, coberturas, correcciones
- operaciones_especiales (13): fusiones, consolidación, derivados

Ver catálogo: conta pd-acto listar

## Lo que NO hace

- Frontend (PWA) para el operario. Se construye en Fase 4d.
- FTOP + CAS + hipótesis en el worker (simulado como "ok=True" en el demo).
- Presentación oficial de cuentas anuales (Registro Mercantil).
- Modelos 200/303 con formato AEAT.
- Contabilización automática de FIFO/PMP: `valorar_salida_existencias` calcula el coste de salida sobre lotes proporcionados, pero no registra asientos ni define la política por entidad.
- Consolidación multi-PGC (solo PGC_ES cargado).
- Corpus forense con alcance 2027 (MIPYMEs y personas físicas sucesoras): existe almacenamiento y API restringida a administradores, pero sin aislamiento por empresa.

## Arquitectura

    conta_rizoma4/
    ├── contratos/          A+B+C+D (declarativo)
    ├── dominio/            núcleo epistémico, casos de uso, presentación y fiscal
    ├── operativo/          hash chain + mapeo (POC legacy, deprecated)
    ├── partida_doble/      partida doble real + libros
    ├── actos/              115 actos en 14 grupos
    ├── custodia/           obras, operarios, leases, documentos
    ├── consolidacion/      grupo clásico
    ├── config/             empresas.yaml + tipos de cambio BCE
    ├── api/                FastAPI
    │   └── routers/        asientos, empresas, verificar, leases,
    │                       obras, operarios, documentos
    ├── operaciones.py      helper crear_acto_por_codigo
    ├── cli.py              CLI unificado (POC + partida doble)
    └── cli_pd.py           comandos de partida doble

## Tests

Suite segura por defecto (no conecta a PostgreSQL):

    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/ruben/MyProyecto/rizoma4:/home/ruben/MyProyecto/conta-rizoma4 \
    .venv/bin/python -m pytest -q

Resultado verificado el 2026-11-26 tras la ronda de roles y el cableado de delegación: **371 passed, 185 deselected, 1 warning in 2.81s**. `tests/conftest.py` marca como `integration` los módulos que acceden a PostgreSQL; `pyproject.toml` los excluye por defecto. `make test` equivale a `pytest -m "not integration and not slow"`.

Suite de integración (sólo contra un PostgreSQL aislado con rol `test`):

    CONTA_PG_URL='postgresql://test@/test?host=/ruta/al/socket&port=55432' \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/ruben/MyProyecto/rizoma4:/home/ruben/MyProyecto/conta-rizoma4 \
    .venv/bin/python -m pytest -m integration -q

`pytest -m integration --collect-only -q` recoge **185 pruebas**. Ejecución real verificada el 2026-11-26 contra un clúster PostgreSQL efímero con DDL y migraciones aisladas, datos PGC sintéticos y sin el trigger de mantenimiento de `004_inmutabilidad.sql`: **185 passed, 371 deselected, 1 warning in 13.32s**. La URL usada fue `postgresql://test@/test?host=/tmp/opencode/pgtest-conta/sock&port=55432`; no se usaron datos reales ni PostgreSQL de producción. Antes: **47 failed, 392 passed, 5 skipped, 1 warning, 91 errors**, causados por esa falta de rol, la ausencia de `config/empresas.yaml` y 12 pruebas heredadas sin `autorizacion_id`; esos puntos quedaron corregidos.

Las delegaciones de `aux_obra` se gestionan de forma local y consciente con `scripts/gestionar_permiso.py`, subcomandos `conceder` y `revocar` y flag `--confirmar`; el ledger usado es `dominio_evento`. La API consulta ese ledger en crear/visar/aprobar asientos.

Suites focales verificadas: **138 passed** en dominio/adaptadores/API simulada y **57 passed** en actos avanzados. Copia `config/empresas.yaml.example` a `config/empresas.yaml` en cada entorno; el fichero real está ignorado por Git. Consulta `PLAN_CIERRE_BRECHAS.md` para el detalle y ejecuta siempre el alcance que vayas a modificar.

## Doctrina

PGC párrafo 4: en la contabilización de las operaciones se atenderá a
su realidad económica y no sólo a su forma jurídica.

Rizoma4 §6 #37: La forma es el vehículo de la sustancia. Sin forma no
hay sustancia procesable.

conta-rizoma4 lo materializa: cada asiento tiene su párrafo del PGC que
lo justifica, su hash encadenado, y su cadena de mando. Si alguien
manipula un acto, conta pd-verificar lo detecta.

La cadena de custodia (obras, operarios, leases, estados) usa lo que
rizoma4 ya tiene (CAS, ledger, PAdES, TSA, Merkle).
