# =============================================================================
# MÓDULO 2 - LECCIÓN 3: Pandas — Introducción
# =============================================================================
# pandas es la librería central del stack de datos en Python.
# Instalar: pip install pandas
#
# Conceptos clave:
#   Series      -> columna (array 1D con índice)
#   DataFrame   -> tabla (colección de Series con índice compartido)
#
# En datos: reemplaza casi todo lo que se hacía con CSV manual.
# =============================================================================

import pandas as pd
import os

DATOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")
os.makedirs(DATOS_DIR, exist_ok=True)


# =============================================================================
# PARTE A — Series
# =============================================================================

# --- A1: Crear Series ---

precios = pd.Series([12.50, 8.00, 25.00, 9.75, 3.00])
print(precios)
print(f"\nTipo: {type(precios)}")
print(f"dtype: {precios.dtype}")

# Series con índice personalizado
precios_con_idx = pd.Series(
    [12.50, 8.00, 25.00],
    index=["arroz", "leche", "aceite"]
)
print(f"\nPrecio del arroz: {precios_con_idx['arroz']}")

# --- A2: Operaciones vectorizadas (sin for) ---

cantidades = pd.Series([100, 200, 80, 150, 300])
totales = precios * cantidades     # multiplicación elemento a elemento
print(f"\nTotales:\n{totales}")
print(f"Suma total: {totales.sum():.2f}")
print(f"Promedio:   {totales.mean():.2f}")


# =============================================================================
# PARTE B — DataFrame
# =============================================================================

# --- B1: Crear DataFrame desde dict ---

datos = {
    "producto":  ["arroz", "leche", "aceite", "azucar", "sal"],
    "cantidad":  [100, 200, 80, 150, 300],
    "precio":    [12.50, 8.00, 25.00, 9.75, 3.00],
    "region":    ["norte", "sur", "norte", "este", "sur"],
    "activo":    [True, True, False, True, True],
}
df = pd.DataFrame(datos)
print(df)
print(f"\nForma: {df.shape}")      # (filas, columnas)
print(f"Columnas: {list(df.columns)}")


# --- B2: Inspección rápida ---

print(df.head(3))         # primeras 3 filas
print(df.tail(2))         # últimas 2 filas
print(df.info())          # tipos y nulos
print(df.describe())      # estadísticas de columnas numéricas
print(df.dtypes)          # tipo de cada columna


# --- B3: Acceder a columnas y filas ---

# Columna como Series
print(df["producto"])
print(df[["producto", "precio"]])   # múltiples columnas -> DataFrame

# Filas por posición con .iloc
print(df.iloc[0])        # primera fila (Serie)
print(df.iloc[0:3])      # primeras 3 filas

# Filas por índice con .loc
print(df.loc[2])         # fila con índice 2

# Celda individual
print(df.at[1, "precio"])       # fila 1, columna "precio"
print(df.iloc[1, 2])            # fila 1, columna índice 2


# --- B4: Agregar y eliminar columnas ---

df["total"] = df["cantidad"] * df["precio"]          # nueva columna calculada
df["precio_con_iva"] = (df["precio"] * 1.16).round(2)

df = df.drop(columns=["precio_con_iva"])             # eliminar columna

print(df)


# =============================================================================
# PARTE C — Leer y escribir archivos
# =============================================================================

# --- C1: Guardar y leer CSV ---

ruta_csv = os.path.join(DATOS_DIR, "ventas_pandas.csv")
df.to_csv(ruta_csv, index=False)                      # index=False evita guardar el índice

df_leido = pd.read_csv(ruta_csv)
print(f"\nLeído desde CSV: {df_leido.shape}")


# --- C2: Parámetros útiles de read_csv ---

df2 = pd.read_csv(
    ruta_csv,
    usecols=["producto", "cantidad", "precio"],   # solo estas columnas
    dtype={"cantidad": int, "precio": float},      # forzar tipos
)
print(df2.dtypes)


# --- C3: Excel ---

ruta_excel = os.path.join(DATOS_DIR, "ventas.xlsx")
try:
    df.to_excel(ruta_excel, index=False, sheet_name="ventas")
    df_excel = pd.read_excel(ruta_excel, sheet_name="ventas")
    print(f"\nExcel leído: {df_excel.shape}")
except ImportError:
    print("\nInstala openpyxl para Excel: pip install openpyxl")


# --- C4: JSON ---

ruta_json = os.path.join(DATOS_DIR, "ventas.json")
df.to_json(ruta_json, orient="records", indent=2)
df_json = pd.read_json(ruta_json)
print(f"\nJSON leído: {df_json.shape}")


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# Crea un DataFrame con al menos 6 filas representando un log de ejecución
# de pipelines con columnas:
#   pipeline_id (int), nombre (str), estado (str), filas_procesadas (int), duracion_seg (float)
# Imprime: shape, dtypes, describe(), y las 3 primeras filas.

# TODO:


# EJ-2
# Dado el DataFrame `df` de ventas:
# a) Agrega una columna "descuento" = precio * 0.10 (redondeado a 2 decimales)
# b) Agrega una columna "precio_final" = precio - descuento
# c) Agrega una columna "categoria" con el valor "premium" si precio > 15, "normal" en otro caso
# d) Imprime el DataFrame resultante

# TODO: trabaja sobre df


# EJ-3
# Lee el archivo ventas_pandas.csv.
# Imprime cuántos valores nulos hay por columna (usa .isnull().sum()).
# Luego imprime las filas que tienen al menos un nulo (usa .isnull().any(axis=1)).

# TODO:


# EJ-4
# Accede a:
#   a) La fila del producto "aceite" (usa .loc con condición booleana)
#   b) El precio del primer producto de la región "sur"
#   c) Las columnas "producto" y "total" de las últimas 3 filas

# TODO: trabaja sobre df


# EJ-5 (desafío)
# Guarda el DataFrame df en tres formatos distintos: CSV, JSON y Excel.
# Luego léelos de nuevo y verifica que los tres tienen el mismo shape
# y que la suma de la columna "total" es igual en los tres.
# Imprime un resumen: "CSV ✓ / JSON ✓ / Excel ✓" o con ✗ si fallan.

# TODO:
