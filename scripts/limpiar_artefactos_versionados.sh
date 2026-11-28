#!/usr/bin/env bash
# Elimina del índice git los artefactos que nunca debieron versionarse.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
PATRONES=(
  'scripts/seed_pgc.py.bak_*'
  'pyproject.toml.bak.*'
  '*.whl'
  'mdbtools/'
  'mdb_extraido*/'
  '*.zst'
)
for p in "${PATRONES[@]}"; do
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    echo "git rm --cached $f"
    git rm --cached -r "$f" 2>/dev/null || true
  done < <(git ls-files "$p" 2>/dev/null)
done
echo "✅ Índice limpio. Los ficheros siguen en disco (git status los verá como untracked, ya ignorados)."