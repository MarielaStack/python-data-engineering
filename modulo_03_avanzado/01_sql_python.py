# =============================================================================
# MÓDULO 3 - LECCIÓN 1: SQL con Python
# =============================================================================
# Python tiene soporte nativo para SQLite (sin instalar nada) y se conecta
# a PostgreSQL/MySQL/etc con librerías externas.
#
# Librerías:
#   sqlite3     -> stdlib, ideal para aprender y pruebas locales
#   sqlalchemy  -> ORM + conexión a cualquier motor (pip install sqlalchemy)
#   pandas      -> read_sql / to_sql para mover datos entre DF y BD
#
# En datos: cargar tablas de staging, hacer queries analíticos, upserts.
# =============================================================================

import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos", "pipeline.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


# =============================================================================
# PARTE A — sqlite3 puro
# =============================================================================

# --- A1: Conectar y crear tabla ---

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row   # permite acceder por nombre de columna

cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS ventas (
        id          INTEGER PRIMARY KEY,
        fecha       TEXT    NOT NULL,
        producto    TEXT    NOT NULL,
        region      TEXT    NOT NULL,
        cantidad    INTEGER NOT NULL,
        precio      REAL    NOT NULL,
        total       REAL    GENERATED ALWAYS AS (cantidad * precio) STORED
    )
""")
conn.commit()
print("[DB] Tabla 'ventas' lista")


# --- A2: INSERT --- parametrizado (NUNCA concatenar strings directamente)

registros = [
    ("2024-01-10", "arroz",  "norte", 100, 12.50),
    ("2024-01-15", "leche",  "sur",   200, 8.00),
    ("2024-02-05", "arroz",  "norte", 80,  12.50),
    ("2024-02-20", "aceite", "este",  60,  25.00),
    ("2024-03-01", "leche",  "sur",   150, 8.00),
    ("2024-03-15", "arroz",  "norte", 120, 12.50),
]

cursor.executemany(
    "INSERT OR IGNORE INTO ventas (fecha, producto, region, cantidad, precio) VALUES (?,?,?,?,?)",
    registros
)
conn.commit()
print(f"[DB] {cursor.rowcount} filas insertadas")


# --- A3: SELECT y fetchall ---

cursor.execute("SELECT * FROM ventas ORDER BY fecha")
filas = cursor.fetchall()

for fila in filas:
    # row_factory permite acceso por nombre
    print(f"  {fila['fecha']} | {fila['producto']:8s} | {fila['region']:6s} | total={fila['total']:.2f}")


# --- A4: SELECT con parámetros ---

cursor.execute(
    "SELECT producto, SUM(total) as total_venta FROM ventas WHERE region = ? GROUP BY producto",
    ("norte",)
)
for row in cursor.fetchall():
    print(f"  {row['producto']}: {row['total_venta']:.2f}")


# --- A5: UPDATE y DELETE ---

cursor.execute("UPDATE ventas SET cantidad = 90 WHERE producto = 'aceite' AND region = 'este'")
conn.commit()
print(f"[DB] Filas actualizadas: {cursor.rowcount}")


# --- A6: Contexto manager (auto-commit / rollback) ---

try:
    with conn:   # si hay excepción hace rollback; si no, commit automático
        conn.execute("INSERT INTO ventas (fecha, producto, region, cantidad, precio) VALUES (?,?,?,?,?)",
                     ("2024-03-20", "sal", "norte", 300, 3.00))
    print("[DB] Fila insertada con context manager")
except sqlite3.Error as e:
    print(f"[DB ERROR] {e}")


# =============================================================================
# PARTE B — pandas + SQL
# =============================================================================

# --- B1: Leer directamente a DataFrame ---

df = pd.read_sql("SELECT * FROM ventas", conn)
print(f"\n[pandas] DataFrame desde SQL: {df.shape}")
print(df.head())


# --- B2: Query con pandas ---

df_resumen = pd.read_sql("""
    SELECT
        region,
        COUNT(*)       AS transacciones,
        SUM(total)     AS total_ventas,
        AVG(precio)    AS precio_promedio
    FROM ventas
    GROUP BY region
    ORDER BY total_ventas DESC
""", conn)
print(df_resumen)


# --- B3: Escribir DataFrame a BD ---

nuevas_ventas = pd.DataFrame([
    {"fecha": "2024-04-01", "producto": "azucar", "region": "este",  "cantidad": 90,  "precio": 9.75},
    {"fecha": "2024-04-05", "producto": "arroz",  "region": "norte", "cantidad": 110, "precio": 12.50},
])

nuevas_ventas.to_sql(
    "ventas_staging",
    conn,
    if_exists="replace",   # "append" para agregar sin borrar
    index=False,
)
print(f"\n[pandas] Staging escrito: {len(nuevas_ventas)} filas")


# --- B4: UPSERT manual (INSERT OR REPLACE) ---

def upsert_ventas(conn: sqlite3.Connection, df: pd.DataFrame):
    """Inserta o reemplaza filas existentes por id."""
    placeholders = ", ".join(["?"] * len(df.columns))
    columnas = ", ".join(df.columns)
    sql = f"INSERT OR REPLACE INTO ventas ({columnas}) VALUES ({placeholders})"
    conn.executemany(sql, df.itertuples(index=False, name=None))
    conn.commit()

conn.close()


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# Conecta a pipeline.db, crea una tabla "productos" con columnas:
#   codigo TEXT PRIMARY KEY, categoria TEXT, precio_oficial REAL
# Inserta al menos 4 productos con executemany.
# Luego haz un SELECT que muestre todos los productos ordenados por precio_oficial DESC.

# TODO:


# EJ-2
# Escribe una función `total_por_region(conn, region: str) -> float`
# que consulte la base de datos y retorne el total de ventas para una región.
# Si la región no existe, retorna 0.0.

# TODO: def total_por_region(conn, region): ...


# EJ-3
# Lee la tabla ventas a un DataFrame, agrega una columna "trimestre"
# (1-4 según el mes) y escribe el resultado en una nueva tabla "ventas_enriquecidas"
# usando to_sql con if_exists="replace".

# TODO:


# EJ-4
# Implementa `buscar_duplicados(conn, tabla: str, columnas: list) -> pd.DataFrame`
# que use SQL (GROUP BY + HAVING COUNT > 1) para encontrar combinaciones
# duplicadas de las columnas dadas.
# Pruébala con tabla="ventas" y columnas=["fecha", "producto", "region"].

# TODO:


# EJ-5 (desafío)
# Implementa una función `migrar_csv_a_db(ruta_csv: str, tabla: str, conn)`
# que:
#   1. Lea el CSV con pandas
#   2. Limpie nombres de columnas (strip + lower + replace " " por "_")
#   3. Infiera tipos y convierta
#   4. Use to_sql con if_exists="append"
#   5. Retorne el número de filas insertadas
# Pruébala con el archivo ventas_pandas.csv del módulo anterior.

# TODO:
