#!/usr/bin/env bash
# Identifica secretos a rotar. NO los rota por ti.
set -euo pipefail
ROOT="${1:-$(pwd)}"
MARKERS=("MARIADB_PASSWORD" "CONTA_PG_URL" "JWT_SECRET" "SECRET_KEY" "DATABASE_URL")
echo "🔍 Buscando secretos en $ROOT (excluyendo .git, .venv, mdbtools)…"
echo
found=0
for m in "${MARKERS[@]}"; do
  hits=$(grep -RIl --exclude-dir='.git' --exclude-dir='.venv' \
         --exclude-dir='mdbtools' --exclude-dir='node_modules' \
         -E "^[[:space:]]*(export[[:space:]]+)?${m}[[:space:]]*=" \
         "$ROOT" 2>/dev/null || true)
  if [[ -n "$hits" ]]; then
    echo "  $m →"
    echo "$hits" | sed 's/^/    /'
    found=1
  fi
done
echo
if (( found == 0 )); then echo "✅ Ningún marcador encontrado en ficheros rastreados."; fi
cat <<'EOF'
Acciones obligatorias:
  1. Rotar en el proveedor (MariaDB, Postgres, JWT issuer).
  2. Actualizar .env local (NO versionar).
  3. Borrar del histórico git si estuvo commiteado:
       git filter-repo --path .env --invert-paths
  4. Verificar: ./extraer_para_auditoria.sh  (debe abortar si queda .env)
EOF