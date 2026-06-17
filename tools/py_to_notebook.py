"""
Convierte archivos .py con la estructura del curso a notebooks .ipynb.

Reglas de parseo:
  - Bloque # === ... === (cabecera de lección) -> celda Markdown h1 + descripción
  - Bloque # =============...  PARTE / SECCIÓN  -> celda Markdown h2
  - Línea  # --- SECCIÓN N: Nombre ---          -> celda Markdown h3
  - Bloque # EJERCICIOS                         -> celda Markdown separadora
  - Cada bloque # EJ-N                          -> celda Markdown + celda código
  - El resto del código                         -> celdas de código
"""

import json
import os
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers de celda
# ---------------------------------------------------------------------------

def md_cell(source: str) -> dict:
    lines = [l + "\n" for l in source.rstrip().splitlines()]
    if lines:
        lines[-1] = lines[-1].rstrip("\n")
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": lines,
    }


def code_cell(source: str) -> dict:
    lines = [l + "\n" for l in source.rstrip().splitlines()]
    if lines:
        lines[-1] = lines[-1].rstrip("\n")
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": lines,
    }


def notebook(cells: list, kernel: str = "python3") -> dict:
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": kernel,
            },
            "language_info": {"name": "python", "version": "3.10.0"},
        },
        "cells": [c for c in cells if c["source"]],
    }


# ---------------------------------------------------------------------------
# Extractor de cabecera de lección (bloque ===)
# ---------------------------------------------------------------------------

FENCE = re.compile(r"^# ={10,}")
PART  = re.compile(r"^# ={5,}\s*(PARTE [A-Z]|EJERCICIOS)\s*[-—]*\s*(.*)$", re.I)
SEC   = re.compile(r"^# -{3,}\s*(SECCIÓN \d+|PARTE [A-Z])[\s:]*(.+?)\s*-{3,}")
EJ    = re.compile(r"^# (EJ-\d+)")


def strip_comment(line: str) -> str:
    """Quita el prefijo '# ' o '#' de una línea de comentario."""
    if line.startswith("# "):
        return line[2:]
    if line.startswith("#"):
        return line[1:]
    return line


def is_all_comment(block: str) -> bool:
    return all(l.startswith("#") or l.strip() == "" for l in block.splitlines())


# ---------------------------------------------------------------------------
# Parseo principal
# ---------------------------------------------------------------------------

def parse_py(path: str) -> list:
    text   = Path(path).read_text(encoding="utf-8")
    lines  = text.splitlines()
    cells  = []
    i      = 0
    n      = len(lines)

    def flush_code(buf: list):
        src = "\n".join(buf).strip()
        if src:
            cells.append(code_cell(src))

    # --- Cabecera de lección (primer bloque ===) ---
    header_lines = []
    while i < n and (FENCE.match(lines[i]) or lines[i].startswith("# ")):
        header_lines.append(lines[i])
        i += 1
        # termina cuando encontramos una línea vacía después del bloque
        if i < n and lines[i].strip() == "" and len(header_lines) > 3:
            break

    if header_lines:
        # Extraer título y descripción
        content = [strip_comment(l) for l in header_lines
                   if not FENCE.match(l) and l.strip() not in ("#", "")]
        title = ""
        desc  = []
        for c in content:
            c = c.strip()
            if not c:
                continue
            if not title:
                title = c
            else:
                desc.append(c)
        md = f"# {title}\n"
        if desc:
            md += "\n" + "\n".join(desc)
        cells.append(md_cell(md))

    # --- Cuerpo del archivo ---
    code_buf = []

    while i < n:
        line = lines[i]

        # Bloque separador ===  (PARTE A, PARTE B, EJERCICIOS)
        if FENCE.match(line):
            flush_code(code_buf)
            code_buf = []
            # Recoger el bloque completo
            block = []
            while i < n and (FENCE.match(lines[i]) or lines[i].startswith("# ")):
                block.append(lines[i])
                i += 1
            content = "\n".join(strip_comment(l) for l in block
                                if not FENCE.match(l))
            content = content.strip()
            if content:
                # Detectar si es EJERCICIOS
                if re.search(r"EJERCICIO", content, re.I):
                    cells.append(md_cell("---\n## Ejercicios"))
                else:
                    cells.append(md_cell(f"## {content}"))
            continue

        # Línea separadora de sección ---
        if SEC.match(line):
            flush_code(code_buf)
            code_buf = []
            m = SEC.match(line)
            titulo = m.group(2).strip() if m.group(2) else line.strip()
            cells.append(md_cell(f"### {titulo}"))
            i += 1
            continue

        # Ejercicio individual EJ-N
        if EJ.match(line):
            flush_code(code_buf)
            code_buf = []
            ej_label = EJ.match(line).group(1)
            # Recoger el bloque de comentario del ejercicio
            ej_desc  = []
            while i < n and (lines[i].startswith("#") or lines[i].strip() == ""):
                raw = strip_comment(lines[i]).strip()
                if raw:
                    ej_desc.append(raw)
                i += 1
            # El código del ejercicio (TODO y variables de apoyo) va en la celda de código
            ej_code  = []
            while i < n and lines[i].strip() != "" and not EJ.match(lines[i]) and not FENCE.match(lines[i]):
                ej_code.append(lines[i])
                i += 1
            cells.append(md_cell(f"**{ej_label}** — " + " ".join(ej_desc)))
            stub = "\n".join(ej_code).strip()
            if not stub:
                stub = "# TODO:"
            cells.append(code_cell(stub))
            continue

        # Línea normal -> acumular en código
        code_buf.append(line)
        i += 1

    flush_code(code_buf)
    return cells


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def convertir(py_path: str, nb_path: str = None):
    if nb_path is None:
        nb_path = py_path.replace(".py", ".ipynb")
    cells  = parse_py(py_path)
    nb     = notebook(cells)
    Path(nb_path).write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"  OK  {os.path.basename(py_path):45s} -> {os.path.basename(nb_path)}")


if __name__ == "__main__":
    root = Path(__file__).parent.parent   # raíz del proyecto

    modulos = [
        "modulo_01_basico",
        "modulo_02_intermedio",
        "modulo_03_avanzado",
        "modulo_04_pipelines",
    ]

    total = 0
    for modulo in modulos:
        carpeta = root / modulo
        if not carpeta.exists():
            continue
        archivos = sorted(carpeta.glob("*.py"))
        if not archivos:
            continue
        print(f"\n{modulo}/")
        for py in archivos:
            convertir(str(py))
            total += 1

    print(f"\n{total} notebooks generados.")
