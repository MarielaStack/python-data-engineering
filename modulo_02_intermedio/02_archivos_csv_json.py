# =============================================================================
# MÓDULO 2 - LECCIÓN 2: Archivos CSV y JSON
# =============================================================================
# Leer y escribir CSV y JSON son operaciones diarias en ingeniería de datos.
# Python tiene módulos estándar: `csv` y `json` — sin dependencias externas.
#
# Flujo típico:
#   Fuente (archivo/API) -> leer -> transformar en Python -> escribir -> destino
# =============================================================================

import csv
import json
import os

# Directorio de datos de ejemplo (mismo nivel que el script)
DATOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")
os.makedirs(DATOS_DIR, exist_ok=True)


# =============================================================================
# PARTE A — CSV
# =============================================================================

# --- A1: Escribir un CSV ---

ventas = [
    {"id": 1, "producto": "arroz",  "cantidad": 100, "precio": 12.50, "region": "norte"},
    {"id": 2, "producto": "leche",  "cantidad": 200, "precio": 8.00,  "region": "sur"},
    {"id": 3, "producto": "aceite", "cantidad": 80,  "precio": 25.00, "region": "norte"},
    {"id": 4, "producto": "azucar", "cantidad": 150, "precio": 9.75,  "region": "este"},
    {"id": 5, "producto": "sal",    "cantidad": 300, "precio": 3.00,  "region": "sur"},
]

ruta_ventas = os.path.join(DATOS_DIR, "ventas.csv")

with open(ruta_ventas, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=ventas[0].keys())
    writer.writeheader()       # escribe la fila de encabezados
    writer.writerows(ventas)   # escribe todas las filas

print(f"CSV escrito: {ruta_ventas}")


# --- A2: Leer un CSV ---

with open(ruta_ventas, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)   # cada fila es un dict {columna: valor}
    filas = list(reader)

print(f"\nFilas leídas: {len(filas)}")
for fila in filas:
    print(f"  {fila}")

# IMPORTANTE: csv.DictReader devuelve TODO como string
print(f"\nTipo de 'precio': {type(filas[0]['precio'])}")   # <class 'str'>


# --- A3: Leer y convertir tipos al vuelo ---

def leer_ventas(ruta: str) -> list:
    resultado = []
    with open(ruta, "r", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            resultado.append({
                "id":       int(fila["id"]),
                "producto": fila["producto"],
                "cantidad": int(fila["cantidad"]),
                "precio":   float(fila["precio"]),
                "region":   fila["region"],
            })
    return resultado

ventas_tipadas = leer_ventas(ruta_ventas)
print(f"\nTipo de 'precio' después de parsear: {type(ventas_tipadas[0]['precio'])}")


# --- A4: Escribir solo filas filtradas ---

ruta_norte = os.path.join(DATOS_DIR, "ventas_norte.csv")
ventas_norte = [v for v in ventas_tipadas if v["region"] == "norte"]

with open(ruta_norte, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=ventas_tipadas[0].keys())
    writer.writeheader()
    writer.writerows(ventas_norte)

print(f"\nCSV norte escrito con {len(ventas_norte)} filas")


# =============================================================================
# PARTE B — JSON
# =============================================================================

# --- B1: Escribir JSON ---

config_pipeline = {
    "nombre": "pipeline_ventas",
    "version": "1.2.0",
    "fuentes": [
        {"tipo": "csv",      "ruta": "datos/ventas.csv"},
        {"tipo": "postgres", "host": "db.empresa.com", "tabla": "ordenes"},
    ],
    "destino": {
        "tipo": "s3",
        "bucket": "datalake-prod",
        "prefijo": "ventas/2024/",
    },
    "activo": True,
    "max_filas_lote": 5000,
}

ruta_config = os.path.join(DATOS_DIR, "config.json")
with open(ruta_config, "w", encoding="utf-8") as f:
    json.dump(config_pipeline, f, indent=2, ensure_ascii=False)

print(f"\nJSON escrito: {ruta_config}")


# --- B2: Leer JSON ---

with open(ruta_config, "r", encoding="utf-8") as f:
    config = json.load(f)

print(f"Pipeline: {config['nombre']} v{config['version']}")
print(f"Fuentes: {len(config['fuentes'])}")
for fuente in config["fuentes"]:
    print(f"  tipo={fuente['tipo']}")


# --- B3: json.dumps / json.loads (sin archivo — útil para APIs) ---

datos_dict = {"id": 1, "monto": 500.0, "activo": True}
datos_str = json.dumps(datos_dict)          # dict -> string JSON
print(f"\nJSON string: {datos_str}")

datos_recuperados = json.loads(datos_str)   # string JSON -> dict
print(f"Dict recuperado: {datos_recuperados}")


# --- B4: Manejar tipos no serializables (fecha, Decimal) ---

from datetime import date
from decimal import Decimal

def serializador(obj):
    if isinstance(obj, date):
        return obj.isoformat()      # "2024-03-15"
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Tipo no serializable: {type(obj)}")

evento = {"fecha": date(2024, 3, 15), "monto": Decimal("99.99")}
print(json.dumps(evento, default=serializador))


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# Lee el archivo ventas.csv que ya fue creado, convierte los tipos correctamente
# y calcula el total de ventas (cantidad * precio) por región.
# Escribe el resultado en un nuevo CSV: "resumen_por_region.csv"
# con columnas: region, total_ventas, num_transacciones

# TODO:


# EJ-2
# Crea un archivo JSON llamado "schema_ventas.json" que describa el esquema
# de la tabla ventas con este formato:
#   {"tabla": "ventas", "columnas": [{"nombre": "id", "tipo": "int", "nullable": false}, ...]}
# Incluye las 5 columnas del CSV con los tipos correctos.

# TODO:


# EJ-3
# Lee config.json y modifica el campo "max_filas_lote" a 10000.
# Agrega una nueva fuente: {"tipo": "api", "url": "https://api.empresa.com/ventas"}
# Guarda el archivo actualizado.

# TODO:


# EJ-4
# Escribe una función `csv_a_json(ruta_csv: str, ruta_json: str)` que:
#   1. Lea un CSV
#   2. Intente convertir cada valor al tipo más apropiado
#      (int si es entero, float si es decimal, bool si es "True"/"False", str en otro caso)
#   3. Guarde como JSON array
# Pruébala con ventas.csv.

# TODO: def csv_a_json(ruta_csv, ruta_json): ...


# EJ-5 (desafío)
# Implementa un "append seguro" a CSV:
#   `def agregar_filas_csv(ruta: str, nuevas_filas: list, crear_si_no_existe=True)`
# Si el archivo no existe y crear_si_no_existe=True, créalo con encabezado.
# Si el archivo ya existe, agrega las filas SIN repetir el encabezado.
# Si nuevas_filas está vacío, no hace nada.
# Verifica que las columnas de nuevas_filas coincidan con el encabezado existente
# (si no coinciden, lanza ValueError).

# TODO:
