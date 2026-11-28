#!/usr/bin/env python3
"""Inyecta leer_origen() real desde el .md de auditoría en scripts/seed_pgc.py.

Delimitación robusta: el cuerpo de leer_origen va desde
`def leer_origen(cur)` hasta el siguiente `def`/`class`/`if __name__` de
primer nivel (sin depender de que la última línea sea `return datos`).
"""
import re
import sys
from pathlib import Path

MD = Path.home() / "MyProyecto/trasiegos/extraccion_para_auditoria_conta-rizoma4.md"
TARGET = Path("scripts/seed_pgc.py")

# ── 0. Diagnóstico ────────────────────────────────────────────────────────
print(f"MD:     {MD}")
print(f"        existe={MD.is_file()}")
print(f"TARGET: {TARGET.resolve()}")
print(f"        existe={TARGET.is_file()}")
if not MD.is_file():
    sys.exit("❌ No encuentro el .md")
if not TARGET.is_file():
    sys.exit("❌ No encuentro seed_pgc.py (ejecútame desde la raíz del proyecto)")

md_text = MD.read_text(encoding="utf-8")
print(f"MD size: {len(md_text)} bytes, {md_text.count(chr(10))} líneas")

# ── 1. Localizar la sección `### `scripts/seed_pgc.py`` ──────────────────
patron_seccion = re.compile(
    r"###\s+`scripts/seed_pgc\.py`\s*\n+```python\n(.*?)\n```",
    re.DOTALL,
)
m = patron_seccion.search(md_text)
if m:
    bloque = m.group(1)
    print(f"✓ Sección `scripts/seed_pgc.py` encontrada: {len(bloque.splitlines())} líneas")
else:
    print("✗ Patrón estricto no encontró la sección. Fallback: uso TODO el .md")
    n_defs = len(re.findall(r"^def leer_origen\(cur\)", md_text, re.MULTILINE))
    print(f"  Apariciones de `def leer_origen(cur)` en el .md: {n_defs}")
    if n_defs != 1:
        sys.exit(f"❌ Esperaba 1 aparición, hay {n_defs}")
    bloque = md_text

# ── 2. Localizar `def leer_origen` en el bloque ───────────────────────────
start_m = re.search(r"^def leer_origen\(cur\)", bloque, re.MULTILINE)
if not start_m:
    # Intento B: por si el .md no tiene el tipo `cur` literal
    start_m = re.search(r"^def leer_origen\(", bloque, re.MULTILINE)
if not start_m:
    sys.exit("❌ `def leer_origen(` no encontrado en el bloque")
start_idx = start_m.start()

# ── 3. Delimitar fin: siguiente `def`/`class`/`if __name__` de primer nivel ──
next_m = re.search(
    r"^(?:def |class |if __name__)",
    bloque[start_idx + 1:],
    re.MULTILINE,
)
end_idx = (start_idx + 1 + next_m.start()) if next_m else len(bloque)

leer_origen_real = bloque[start_idx:end_idx].rstrip()
n_lineas = len(leer_origen_real.splitlines())
print(f"✓ leer_origen extraída: {n_lineas} líneas")
print(f"  Primera: {leer_origen_real.splitlines()[0]!r}")
print(f"  Última:  {leer_origen_real.splitlines()[-1]!r}")
if n_lineas < 50:
    sys.exit(f"❌ Extracción sospechosamente corta ({n_lineas} líneas). Abortar.")

# ── 4. Sustituir el placeholder en seed_pgc.py ────────────────────────────
lines = TARGET.read_text(encoding="utf-8").splitlines(keepends=True)
start = end = None
for i, line in enumerate(lines):
    if start is None and line.startswith("def leer_origen(cur) -> dict:"):
        start = i
    if start is not None and "NotImplementedError" in line \
       and ("Copiar leer_origen" in line or "PENDIENTE" in line):
        end = i
        break

if start is None:
    sys.exit("❌ No encuentro `def leer_origen(cur) -> dict:` en seed_pgc.py")
if end is None:
    sys.exit(f"❌ Encontré la def (línea {start+1}) pero no el NotImplementedError asociado")
print(f"✓ Placeholder en líneas {start + 1}–{end + 1} ({end - start + 1} líneas)")

new_lines = lines[:start] + [leer_origen_real + "\n"] + lines[end + 1:]
TARGET.write_text("".join(new_lines), encoding="utf-8")
print(f"✅ Inyectado. Fichero resultante: {len(new_lines)} líneas")