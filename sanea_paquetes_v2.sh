#!/usr/bin/env bash
# sanea_paquetes_v2.sh
# ----------------------------------------------------------------------------
# Sanea el empaquetado de CONTA-RIZOMA4.
#
# Contexto confirmado por dir -R:
#   - Todos los subpaquetes Python YA tienen __init__.py.
#   - conta_rizoma4/frontend/ contiene SOLO assets estáticos (HTML/JS/CSS).
#     NO debe llevar __init__.py ni empaquetarse como paquete Python.
#
# Este script:
#   1. Verifica que frontend/ no tenga __init__.py (y lo rechaza si lo tuviera).
#   2. Sustituye el bloque [tool.setuptools] por [tool.setuptools.packages.find]
#      con exclusión explícita de frontend.
#   3. Reconstruye la rueda.
#   4. Verifica que los 12 subpaquetes Python estén presentes.
#
# Uso:
#   cd ~/MyProyecto/conta-rizoma4
#   chmod +x sanea_paquetes_v2.sh
#   ./sanea_paquetes_v2.sh
# ----------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

PAQUETE="conta_rizoma4"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

echo "=== [1/5] Verificación previa ==="

# 1a. Confirmar que frontend/ NO tiene __init__.py
if [ -f "${PAQUETE}/frontend/__init__.py" ]; then
  echo "  ERROR: ${PAQUETE}/frontend/__init__.py existe."
  echo "  frontend/ es un directorio de assets estáticos y no debe ser paquete Python."
  echo "  Elimínalo manualmente antes de continuar:"
  echo "    rm ${PAQUETE}/frontend/__init__.py"
  exit 1
fi
echo "  OK: frontend/ no tiene __init__.py (es assets estáticos, correcto)."

# 1b. Listar subpaquetes Python esperados
ESPERADOS=(
  actos api api/routers config consolidacion contratos
  corpus_forense cuentas_anuales_oficiales custodia
  modelos_aeat operativo partida_doble
)
echo "  Subpaquetes Python a verificar:"
for sub in "${ESPERADOS[@]}"; do
  if [ -f "${PAQUETE}/${sub}/__init__.py" ]; then
    echo "    OK   ${sub}/"
  else
    echo "    FALTA __init__.py en ${sub}/"
    echo "  ERROR: subpaquete incompleto. Abortando."
    exit 1
  fi
done

echo ""
echo "=== [2/5] Respaldo de pyproject.toml ==="
if [ ! -f "pyproject.toml" ]; then
  echo "ERROR: no se encuentra pyproject.toml en $ROOT" >&2
  exit 1
fi
cp "pyproject.toml" "pyproject.toml.bak.${TIMESTAMP}"
echo "  Respaldo: pyproject.toml.bak.${TIMESTAMP}"

echo ""
echo "=== [3/5] Actualizando pyproject.toml ==="
python3 - <<'PY'
import re, pathlib

p = pathlib.Path("pyproject.toml")
texto = p.read_text()

# Eliminar el bloque [tool.setuptools] con su lista 'packages = [...]'
nuevo = re.sub(
    r"\[tool\.setuptools\]\s*\npackages\s*=\s*\[[^\]]*\]\s*\n?",
    "",
    texto,
    flags=re.MULTILINE | re.DOTALL,
)

# Añadir el nuevo bloque de descubrimiento automático
bloque_nuevo = (
    "\n"
    "[tool.setuptools.packages.find]\n"
    'where = ["."]\n'
    'include = ["conta_rizoma4*"]\n'
    'exclude = [\n'
    '    "tests*", "tests.*",\n'
    '    "old*", "old.*",\n'
    '    "docs*", "doc*",\n'
    '    "scripts*", "scripts.*",\n'
    '    "data*", "data.*",\n'
    '    "mdbtools*", "mdbtools.*",\n'
    '    "mdb_extraido*", "mdb_extraido.*",\n'
    '    "conta_rizoma4.frontend",\n'
    '    "conta_rizoma4.frontend.*",\n'
    ']\n'
)

if "[tool.setuptools.packages.find]" not in nuevo:
    nuevo = nuevo.rstrip() + "\n" + bloque_nuevo

p.write_text(nuevo)
print("  pyproject.toml actualizado.")
print("  Nota: frontend/ excluido explícitamente del empaquetado.")
PY

echo ""
echo "=== [4/5] Reconstruyendo la rueda ==="
rm -rf build/ "${PAQUETE}.egg-info" dist/
pip wheel . --no-deps --no-build-isolation -w dist/ >/dev/null
WHEEL=$(ls dist/*.whl 2>/dev/null | head -n1)
if [ -z "$WHEEL" ]; then
  echo "ERROR: no se generó ninguna rueda." >&2
  exit 1
fi
echo "  Rueda generada: $WHEEL"

echo ""
echo "=== [5/5] Verificando contenido de la rueda ==="
echo "  Subpaquetes presentes en la rueda:"
CONTENIDO=$(unzip -l "$WHEEL" | awk '{print $4}' | grep "^${PAQUETE}/" | grep -v "/__pycache__/" | sed 's|/[^/]*$||' | sort -u)
echo "$CONTENIDO" | sed 's|^|    |'

echo ""
echo "=== Comprobaciones críticas ==="

# Verificar que los 12 subpaquetes están en la rueda
FALTAN=0
for sub in "${ESPERADOS[@]}"; do
  if ! echo "$CONTENIDO" | grep -q "^${PAQUETE}/${sub}$"; then
    echo "  FALTA en la rueda: ${sub}/"
    FALTAN=$((FALTAN + 1))
  fi
done

# Verificar que frontend NO está en la rueda
if echo "$CONTENIDO" | grep -q "^${PAQUETE}/frontend$"; then
  echo "  ERROR: frontend/ fue empaquetado (no debería)."
  FALTAN=$((FALTAN + 1))
else
  echo "  OK: frontend/ NO empaquetado (correcto)."
fi

if [ $FALTAN -eq 0 ]; then
  echo ""
  echo "=== ÉXITO: rueda completa y correcta ==="
  echo ""
  echo "Siguiente paso: prueba de instalación limpia."
  echo "Ejecuta manualmente:"
  echo "  python3 -m venv /tmp/conta-limpio"
  echo "  /tmp/conta-limpio/bin/pip install $WHEEL"
  echo "  /tmp/conta-limpio/bin/conta --help"
  echo ""
  echo "Y verifica imports críticos:"
  for sub in actos api partida_doble operativo custodia config consolidacion cuentas_anuales_oficiales modelos_aeat contratos corpus_forense; do
    echo "  /tmp/conta-limpio/bin/python -c 'import conta_rizoma4.${sub}; print(\"OK ${sub}\")'"
  done
else
  echo ""
  echo "=== FALLO: faltan $FALTAN subpaquetes ==="
  echo "Revisa la salida anterior y corrige antes de continuar."
  exit 1
fi