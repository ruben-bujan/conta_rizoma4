.PHONY: test test-integration test-all demo-safe migrate audit

test:
	pytest -m "not integration and not slow"

test-integration:
	pytest -m integration

test-all:
	pytest

demo-safe:
	@test "$$CONTA_DEMO_OK" = "1" || (echo "❌ exporta CONTA_DEMO_OK=1"; exit 1)
	python scripts/demo_completo.py

migrate:
	python scripts/migrate.py

audit:
	./extraer_para_auditoria.sh