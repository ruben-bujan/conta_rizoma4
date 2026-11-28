#!/usr/bin/env python3
"""Recupera leer_origen() del original desde la mejor fuente disponible.

Orden de intentos:
  1) git show HEAD:scripts/seed_pgc.py  (o rama master/main)
  2) git log → primera versión con leer_origen real
  3) scripts/seed_pgc.py.bak_20261119_081538 en disco
  4) Sección '### `scripts/seed_pgc.py.bak_20261119_081538`' del .md de auditoría
  5) Sección '### `scripts/seed_pgc.py`' del .md, si tiene >400 líneas

Si encuentra ≥ 50 líneas, reescribe scripts/seed_pgc.py en su sitio.
Si no, guarda lo que encuentre en /tmp/leer_origen_candidato.py y explica.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "scripts/seed_pgc.py"
MD = Path.home() / "MyProyecto/trasiegos/extraccion_para_auditoria_conta-rizoma4.md"
BAK = ROOT / "scripts/seed_pgc.py.bak_20261119_081538"
MIN_LINEAS = 50


def extraer_leer_origen(bloque: str) -> str | None:
    """Extrae `def leer_origen` hasta el siguiente def/class de primer nivel."""
    m = re.search(r"^def leer_origen\(", bloque, re.MULTILINE)
    if not m:
        return None
    nxt = re.search(r"^(?:def |class |if __name__)",
                    bloque[m.start() + 1:], re.MULTILINE)
    end = m.start() + 1 + nxt.start() if nxt else len(bloque)
    cuerpo = bloque[m.start():end].rstrip()
    if "NotImplementedError" in cuerpo and len(cuerpo.splitlines()) < MIN_LINEAS:
        return None  # es el placeholder, no sirve
    return cuerpo if len(cuerpo.splitlines()) >= MIN_LINEAS else None


def intento_git_head() -> tuple[str | None, str]:
    for ref in ("HEAD", "main", "master"):
        try:
            r = subprocess.run(
                ["git", "show", f"{ref}:scripts/seed_pgc.py"],
                capture_output=True, text=True, timeout=5, check=False,
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            return None, "git no disponible"
        if r.returncode == 0:
            cuerpo = extraer_leer_origen(r.stdout)
            if cuerpo:
                return cuerpo, f"git show {ref}:scripts/seed_pgc.py"
    return None, "git HEAD no tiene leer_origen real"


def intento_git_history() -> tuple[str | None, str]:
    try:
        r = subprocess.run(
            ["git", "log", "--all", "--pretty=%H", "--", "scripts/seed_pgc.py"],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return None, "git no disponible"
    for sha in r.stdout.split():
        rr = subprocess.run(
            ["git", "show", f"{sha}:scripts/seed_pgc.py"],
            capture_output=True, text=True, timeout=5, check=False,
        )
        if rr.returncode == 0:
            cuerpo = extraer_leer_origen(rr.stdout)
            if cuerpo:
                return cuerpo, f"git show {sha[:8]}:scripts/seed_pgc.py"
    return None, "ningún commit tiene leer_origen real"


def intento_bak_disco() -> tuple[str | None, str]:
    if not BAK.is_file():
        return None, f"no existe {BAK.name}"
    cuerpo = extraer_leer_origen(BAK.read_text(encoding="utf-8"))
    return (cuerpo, str(BAK)) if cuerpo else (None, f"{BAK.name} tiene placeholder")


def intento_md_bak() -> tuple[str | None, str]:
    if not MD.is_file():
        return None, f"no existe {MD}"
    txt = MD.read_text(encoding="utf-8")
    m = re.search(
        r"###\s+`scripts/seed_pgc\.py\.bak_[^`]*`\s*\n+```[a-z]*\n(.*?)\n```",
        txt, re.DOTALL,
    )
    if not m:
        return None, "el .md no tiene sección del .bak"
    cuerpo = extraer_leer_origen(m.group(1))
    return (cuerpo, "sección .bak del .md") if cuerpo \
        else (None, "sección .bak del .md tiene placeholder")


def intento_md_principal() -> tuple[str | None, str]:
    if not MD.is_file():
        return None, f"no existe {MD}"
    txt = MD.read_text(encoding="utf-8")
    m = re.search(
        r"###\s+`scripts/seed_pgc\.py`\s*\n+```python\n(.*?)\n```",
        txt, re.DOTALL,
    )
    if not m:
        return None, "el .md no tiene sección de seed_pgc.py"
    cuerpo = extraer_leer_origen(m.group(1))
    return (cuerpo, "sección principal del .md") if cuerpo \
        else (None, "sección principal del .md tiene placeholder")


INTENTOS = [
    ("git HEAD",          intento_git_head),
    ("git history",       intento_git_history),
    ("bak en disco",      intento_bak_disco),
    ("bak en .md",        intento_md_bak),
    (".md principal",     intento_md_principal),
]

if __name__ == "__main__":
    print(f"ROOT:   {ROOT}")
    print(f"TARGET: {TARGET}")
    print()
    elegido: tuple[str, str] | None = None
    for nombre, fn in INTENTOS:
        print(f"── Intento: {nombre} ──")
        cuerpo, detalle = fn()
        if cuerpo:
            n = len(cuerpo.splitlines())
            print(f"  ✅ {n} líneas ← {detalle}")
            print(f"     Primera: {cuerpo.splitlines()[0]!r}")
            print(f"     Última:  {cuerpo.splitlines()[-1]!r}")
            elegido = (cuerpo, detalle)
            break
        else:
            print(f"  ✗ {detalle}")

    if not elegido:
        print("\n❌ NINGUNA fuente tiene leer_origen real. No puedo continuar.")
        print("   Opciones:")
        print("   a) Restaura scripts/seed_pgc.py desde una copia de seguridad externa.")
        print("   b) Ejecuta: git log --all -- scripts/seed_pgc.py  y pásame la lista.")
        sys.exit(1)

    cuerpo, fuente = elegido
    lines = TARGET.read_text(encoding="utf-8").splitlines(keepends=True)
    start = end = None
    for i, line in enumerate(lines):
        if start is None and line.startswith("def leer_origen(cur) -> dict:"):
            start = i
        if start is not None and "NotImplementedError" in line:
            end = i
            break
    if start is None or end is None:
        sys.exit(f"❌ No encuentro el placeholder en {TARGET}")
    print(f"\n✓ Placeholder en líneas {start+1}–{end+1}")
    new_lines = lines[:start] + [cuerpo + "\n"] + lines[end + 1:]
    TARGET.write_text("".join(new_lines), encoding="utf-8")
    print(f"✅ Inyectado desde: {fuente}")
    print(f"✅ {TARGET.name} resultante: {len(new_lines)} líneas")