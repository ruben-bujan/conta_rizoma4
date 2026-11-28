# Manual de instalación — conta-rizoma4

1. Instalar rizoma4: `cd ~/MyProyecto/rizoma4 && pip install -e .`
2. Instalar conta-rizoma4: `pip install conta_rizoma4-0.1.0-py3-none-any.whl` o `pip install -e '.[test]'`
3. Copiar `config/conta_config.json.example` → `config/conta_config.json` y ajustar.
4. Seed PGC: `python scripts/seed_pgc.py` (requiere MARIADB_PASSWORD)
5. DDL: aplicar scripts/ddl_*.sql en PostgreSQL
6. Arrancar: `uvicorn conta_rizoma4.api.main:app --port 8001`
