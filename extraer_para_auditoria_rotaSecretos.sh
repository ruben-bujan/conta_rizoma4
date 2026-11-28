#!/usr/bin/env bash
# extraer_para_auditoria.sh — v2 (auditoría doctrinal)
# Genera un único .md con el código del proyecto.
# - Soporta .auditignore (un patrón por línea, formato glob).
# - Excluye secretos (.env, *.pem, *.key), dependencias vendored (mdbtools/),
#   artefactos (*.whl, *.zst, *.bak*), binarios y DBs.
# - Falla (exit 1) si detecta .env en el árbol: obliga a rotar antes de extraer.
set -uo pipefail

SOURCE_DIR="${1:-${AUDIT_SOURCE:-$(pwd)}}"
SOURCE_DIR="$(cd "$SOURCE_DIR" 2>/dev/null && pwd)" || {
  echo "❌ Directorio origen no existe: ${1:-$(pwd)}" >&2; exit 1
}
BASE_NAME="$(basename "$SOURCE_DIR")"
OUTPUT_DIR="${AUDIT_OUTPUT_DIR:-$HOME/MyProyecto/trasiegos}"
OUTPUT_FILE="$OUTPUT_DIR/extraccion_para_auditoria_${BASE_NAME}.md"

# ── Guardia de secretos ────────────────────────────────────────────────────
SECRET_FOUND=()
while IFS= read -r -d '' s; do SECRET_FOUND+=("$s"); done < <(
  find "$SOURCE_DIR" -maxdepth 3 -type f \
    \( -name '.env' -o -name '*.env' -o -name 'secrets.*' \
       -o -name '*.pem' -o -name '*.key' \) -print0 2>/dev/null
)
if (( ${#SECRET_FOUND[@]} > 0 )); then
  echo "❌ Detectados posibles secretos. Rótalos y bórralos ANTES de extraer:" >&2
  for s in "${SECRET_FOUND[@]}"; do echo "   $s" >&2; done
  echo "   → Lanza: scripts/rotate_secrets.sh $SOURCE_DIR" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"
: > "$OUTPUT_FILE"
echo "🔍 Origen: $SOURCE_DIR"
echo "📝 Salida: $OUTPUT_FILE"

# ── Exclusiones ────────────────────────────────────────────────────────────
EXCLUDE_DIRS=(
  '.venv' 'venv' 'env' 'virtualenv'
  'backup' 'backups' 'old' 'tmp' 'temp'
  '__pycache__' '*.egg-info'
  'report' 'reports'
  'input*' 'output*'
  '.git' '.git*'
  'experimental'
  'dist' 'build' 'htmlcov' '.tox' '.nox'
  'docs' 'doc'
  'data'
  '*pytest*' '*cache*' '.cache' '.mypy_cache' '.ruff_cache'
  'node_modules'
  # v2: dependencias vendored y artefactos de build
  'mdbtools' 'mdb_extraido*'
  '.deps' '.libs' 'build-aux' 'pkg' 'po' 'm4'
  'site-packages'
)

EXCLUDE_EXTS=(
  # docs / metadatos
  'json' 'txt' 'md' 'csv' 'bk' 'bak' 'bak_*'
  # bases de datos
  'mdb' 'accdb' 'db' 'sqlite' 'sqlite3'
  'sql' 'dump' 'psql' 'pgsql'
  # binarios / artefactos
  'pyc' 'pyo' 'so' 'o' 'a' 'dll' 'exe' 'bin'
  'whl' 'egg'
  'zip' 'tar' 'gz' 'bz2' 'xz' '7z' 'rar' 'zst' 'tgz'
  'png' 'jpg' 'jpeg' 'gif' 'svg' 'ico' 'bmp' 'tiff' 'webp'
  'pdf' 'docx' 'xlsx' 'pptx' 'odt' 'ods'
  'woff' 'woff2' 'ttf' 'otf' 'eot'
  'mp3' 'mp4' 'avi' 'mov' 'wav' 'ogg' 'flac'
  # build artifacts
  'la' 'lo' 'lai' 'Po' 'Plo' 'T' 'ver' 'expsym'
  'log' 'status' 'rpath' 'rpath~'
  'in' 'am' 'm4'
)

# ── .auditignore (patrones glob adicionales) ───────────────────────────────
if [[ -f "$SOURCE_DIR/.auditignore" ]]; then
  while IFS= read -r line; do
    line="${line%%#*}"
    line="${line//[[:space:]]/}"
    [[ -z "$line" ]] && continue
    if [[ "$line" == */ ]]; then
      EXCLUDE_DIRS+=("${line%/}")
    else
      EXCLUDE_EXTS+=("$line")
    fi
  done < "$SOURCE_DIR/.auditignore"
fi

# ── Detección de lenguaje ──────────────────────────────────────────────────
lang_for() {
  case "${1##*.}" in
    py)             echo python ;;
    js|mjs|cjs)     echo javascript ;;
    ts)             echo typescript ;;
    tsx)            echo tsx ;;
    jsx)            echo jsx ;;
    sh|bash|zsh)    echo bash ;;
    yml|yaml)       echo yaml ;;
    toml)           echo toml ;;
    ini|cfg|conf)   echo ini ;;
    html|htm)       echo html ;;
    css)            echo css ;;
    scss|sass)      echo scss ;;
    java)           echo java ;;
    go)             echo go ;;
    rs)             echo rust ;;
    php)            echo php ;;
    rb)             echo ruby ;;
    c|h)            echo c ;;
    cpp|cc|cxx|hpp) echo cpp ;;
    cs)             echo csharp ;;
    *)              echo "" ;;
  esac
}

# ── Construcción de find ───────────────────────────────────────────────────
PRUNE_ARGS=(); for d in "${EXCLUDE_DIRS[@]}"; do PRUNE_ARGS+=( -o -name "$d" ); done
PRUNE_ARGS=("${PRUNE_ARGS[@]:1}")
EXT_ARGS=(); for e in "${EXCLUDE_EXTS[@]}"; do EXT_ARGS+=( ! -iname "*.$e" ); done

TMP_LIST="$(mktemp)"; trap 'rm -f "$TMP_LIST"' EXIT
echo "⏳ Buscando archivos…"
find "$SOURCE_DIR" \
  -type d \( "${PRUNE_ARGS[@]}" \) -prune -o \
  -type f "${EXT_ARGS[@]}" \
  ! -name '.env' ! -name '*.env' ! -name 'secrets.*' \
  ! -name '*.pem' ! -name '*.key' \
  ! -path "$OUTPUT_DIR/*" ! -path "$OUTPUT_FILE" \
  -print0 > "$TMP_LIST"

COUNT=0; while IFS= read -r -d '' _; do COUNT=$((COUNT + 1)); done < "$TMP_LIST"
echo "   Archivos a procesar: $COUNT"
if (( COUNT == 0 )); then echo "⚠️  Sin archivos. Revisa .auditignore y exclusiones." >&2; exit 0; fi

# ── Cabecera + índice ──────────────────────────────────────────────────────
{
  echo "# Extracción de código para auditoría — $BASE_NAME"
  echo
  echo "- **Origen:** \`$SOURCE_DIR\`"
  echo "- **Fecha:** $(date '+%Y-%m-%d %H:%M:%S')"
  echo "- **Archivos incluidos:** $COUNT"
  echo
  echo "## Índice"; echo
  while IFS= read -r -d '' f; do echo "- \`${f#"$SOURCE_DIR"/}\`"; done < "$TMP_LIST"
  echo; echo "---"; echo; echo "## Contenidos"; echo
} >> "$OUTPUT_FILE"

# ── Contenidos ─────────────────────────────────────────────────────────────
N=0
while IFS= read -r -d '' FILE; do
  REL="${FILE#"$SOURCE_DIR"/}"; LANG="$(lang_for "$FILE")"; N=$((N + 1))
  printf "   [%4d/%4d] %s\n" "$N" "$COUNT" "$REL"
  SIZE=$(stat -c%s "$FILE" 2>/dev/null || echo 0)
  {
    echo "### \`$REL\`"; echo
    if (( SIZE > 5242880 )); then
      echo "_[archivo > 5 MB, omitido]_"
    elif head -c 4096 "$FILE" | tr -d -c '\000' | grep -q . ; then
      echo "_[binario omitido]_"
    else
      echo '```'"$LANG"
      cat "$FILE" 2>/dev/null || echo "[error leyendo]"
      echo; echo '```'
    fi
    echo
  } >> "$OUTPUT_FILE"
done < "$TMP_LIST"

echo; echo "✅ Extracción completada — $COUNT archivos → $OUTPUT_FILE"