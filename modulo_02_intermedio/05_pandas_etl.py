# =============================================================================
# MÓDULO 2 - LECCIÓN 5: Pipeline ETL completo con Pandas
# =============================================================================
# ETL = Extract → Transform → Load
#
# Esta lección integra todo lo visto y simula un pipeline real:
#   1. Extracción desde múltiples fuentes (CSV + JSON)
#   2. Transformación: limpieza, tipado, enriquecimiento, validación
#   3. Carga: escritura de resultado + reporte de calidad
# =============================================================================

import pandas as pd
import json
import os
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR  = os.path.join(BASE, "datos", "input")
OUTPUT_DIR = os.path.join(BASE, "datos", "output")
os.makedirs(INPUT_DIR,  exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# =============================================================================
# PASO 0 — Generar datos de entrada (simula fuentes reales)
# =============================================================================

# Fuente 1: ventas_raw.csv (con datos sucios)
ventas_raw_data = """id,fecha,producto,region,cantidad,precio,vendedor_id
1,2024-01-10,arroz,norte,100,12.50,V01
2,2024-01-15,Leche ,SUR,200,8.00,V02
3,2024-02-05,ARROZ,Norte,-80,12.50,V01
4,2024-02-20,aceite,este,,25.00,V03
5,2024-03-01,leche,sur,150,abc,V02
6,2024-03-15,arroz,norte,120,12.50,V01
7,2024-01-22,azucar,este,90,9.75,V04
8,2024-03-28,aceite,sur,70,25.00,V03
9,2024-02-10,sal,norte,300,3.00,
10,2024-03-05,arroz,norte,110,12.50,V01
"""

with open(os.path.join(INPUT_DIR, "ventas_raw.csv"), "w", encoding="utf-8") as f:
    f.write(ventas_raw_data.strip())

# Fuente 2: catalogo_productos.json
catalogo = [
    {"codigo": "arroz",  "categoria": "granos",    "precio_oficial": 12.50},
    {"codigo": "leche",  "categoria": "lacteo",    "precio_oficial": 8.00},
    {"codigo": "aceite", "categoria": "aceite",    "precio_oficial": 25.00},
    {"codigo": "azucar", "categoria": "dulce",     "precio_oficial": 9.75},
    {"codigo": "sal",    "categoria": "condimento","precio_oficial": 3.00},
]
with open(os.path.join(INPUT_DIR, "catalogo.json"), "w") as f:
    json.dump(catalogo, f, indent=2)

print("Datos de entrada generados.\n")


# =============================================================================
# EXTRACT
# =============================================================================

def extraer_ventas(ruta: str) -> pd.DataFrame:
    df = pd.read_csv(ruta, dtype=str)    # leer todo como string primero
    print(f"[EXTRACT] {len(df)} filas leídas desde {os.path.basename(ruta)}")
    return df

def extraer_catalogo(ruta: str) -> pd.DataFrame:
    with open(ruta, "r") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    print(f"[EXTRACT] {len(df)} productos en catálogo")
    return df

df_ventas   = extraer_ventas(os.path.join(INPUT_DIR, "ventas_raw.csv"))
df_catalogo = extraer_catalogo(os.path.join(INPUT_DIR, "catalogo.json"))


# =============================================================================
# TRANSFORM
# =============================================================================

def transformar(df: pd.DataFrame, catalogo: pd.DataFrame) -> tuple:
    """Retorna (df_limpio, df_rechazados)."""

    errores = []

    # T1: Normalizar strings — strip y lower
    for col in ["producto", "region", "vendedor_id"]:
        df[col] = df[col].str.strip().str.lower()

    # T2: Parsear fecha
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

    # T3: Convertir tipos numéricos
    df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce")
    df["precio"]   = pd.to_numeric(df["precio"],   errors="coerce")
    df["id"]       = pd.to_numeric(df["id"],        errors="coerce").astype("Int64")

    # T4: Detectar y separar filas con errores
    mascara_errores = (
        df["fecha"].isna()       |
        df["cantidad"].isna()    |
        df["precio"].isna()      |
        (df["cantidad"] <= 0)    |
        (df["precio"] <= 0)
    )

    df_rechazados = df[mascara_errores].copy()
    df_rechazados["motivo_rechazo"] = (
        df_rechazados.apply(_motivo_rechazo, axis=1)
    )
    df_limpio = df[~mascara_errores].copy()

    print(f"[TRANSFORM] Válidos: {len(df_limpio)}, Rechazados: {len(df_rechazados)}")

    # T5: Enriquecer con catálogo
    df_limpio = df_limpio.merge(
        catalogo[["codigo", "categoria", "precio_oficial"]],
        left_on="producto",
        right_on="codigo",
        how="left"
    ).drop(columns=["codigo"])

    # T6: Columnas derivadas
    df_limpio["total"]          = df_limpio["cantidad"] * df_limpio["precio"]
    df_limpio["precio_ok"]      = df_limpio["precio"] == df_limpio["precio_oficial"]
    df_limpio["anio"]           = df_limpio["fecha"].dt.year
    df_limpio["mes"]            = df_limpio["fecha"].dt.month
    df_limpio["trimestre"]      = df_limpio["fecha"].dt.quarter

    # T7: Ordenar columnas
    columnas_orden = [
        "id", "fecha", "anio", "mes", "trimestre",
        "producto", "categoria", "region", "vendedor_id",
        "cantidad", "precio", "precio_oficial", "precio_ok", "total",
    ]
    df_limpio = df_limpio[columnas_orden]

    return df_limpio, df_rechazados


def _motivo_rechazo(row) -> str:
    motivos = []
    if pd.isna(row["fecha"]):       motivos.append("fecha inválida")
    if pd.isna(row["cantidad"]):    motivos.append("cantidad no numérica")
    elif row["cantidad"] <= 0:      motivos.append("cantidad <= 0")
    if pd.isna(row["precio"]):      motivos.append("precio no numérico")
    elif row["precio"] <= 0:        motivos.append("precio <= 0")
    return " | ".join(motivos) if motivos else "desconocido"


df_limpio, df_rechazados = transformar(df_ventas, df_catalogo)


# =============================================================================
# LOAD
# =============================================================================

def cargar(df_limpio: pd.DataFrame, df_rechazados: pd.DataFrame, output_dir: str):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Archivo principal
    ruta_ok  = os.path.join(output_dir, f"ventas_limpias_{ts}.csv")
    df_limpio.to_csv(ruta_ok, index=False)
    print(f"[LOAD] Datos limpios -> {os.path.basename(ruta_ok)}")

    # Archivo de rechazados
    if len(df_rechazados) > 0:
        ruta_err = os.path.join(output_dir, f"rechazados_{ts}.csv")
        df_rechazados.to_csv(ruta_err, index=False)
        print(f"[LOAD] Rechazados   -> {os.path.basename(ruta_err)}")

    # Resumen por región
    resumen = (df_limpio
        .groupby("region")
        .agg(
            total_ventas=("total", "sum"),
            transacciones=("id", "count"),
            productos_distintos=("producto", "nunique"),
        )
        .round(2)
        .reset_index()
    )
    ruta_res = os.path.join(output_dir, f"resumen_region_{ts}.csv")
    resumen.to_csv(ruta_res, index=False)
    print(f"[LOAD] Resumen región -> {os.path.basename(ruta_res)}")

    # Reporte de calidad (JSON)
    reporte = {
        "timestamp": ts,
        "total_input":     len(df_limpio) + len(df_rechazados),
        "total_validos":   len(df_limpio),
        "total_rechazados": len(df_rechazados),
        "tasa_rechazo_pct": round(len(df_rechazados) / (len(df_limpio) + len(df_rechazados)) * 100, 1),
        "suma_total_ventas": round(df_limpio["total"].sum(), 2),
        "precio_discrepante": int(df_limpio["precio_ok"].eq(False).sum()),
    }
    ruta_rep = os.path.join(output_dir, f"reporte_calidad_{ts}.json")
    with open(ruta_rep, "w") as f:
        json.dump(reporte, f, indent=2)

    print(f"[LOAD] Reporte calidad -> {os.path.basename(ruta_rep)}")
    return reporte


reporte = cargar(df_limpio, df_rechazados, OUTPUT_DIR)

print("\n=== REPORTE FINAL ===")
for k, v in reporte.items():
    print(f"  {k}: {v}")


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# El pipeline actual no maneja vendedor_id nulo (fila 9 tiene vendedor vacío).
# Modifica la función `transformar` para que los registros sin vendedor_id
# se marquen con "desconocido" en lugar de rechazarse.
# Imprime cuántas filas tienen vendedor "desconocido" al final.

# TODO:


# EJ-2
# Agrega al reporte de calidad dos métricas nuevas:
#   - "ventas_por_region": dict {region: total_ventas}
#   - "mes_mayor_venta": int (mes con mayor total acumulado)
# Modifica la función `cargar` para incluirlas.

# TODO:


# EJ-3
# Agrega una etapa T8 en `transformar` que detecte outliers en "total":
# Un registro es outlier si su total supera la media + 2 * desviación estándar.
# Marca esas filas con una columna booleana "es_outlier".
# Imprime cuántos outliers hay y cuáles son.

# TODO:


# EJ-4
# Genera un reporte pivot (tabla cruzada) con:
#   filas = producto, columnas = mes, valores = suma de total
# Guárdalo como "pivot_producto_mes.csv" en el output.
# PISTA: usa pd.pivot_table() o groupby + unstack().

# TODO:


# EJ-5 (desafío — pipeline parametrizable)
# Refactoriza el pipeline en una función `ejecutar_etl(config: dict)` que
# reciba un diccionario de configuración con:
#   {
#     "fuente_ventas":  "ruta al CSV",
#     "fuente_catalogo": "ruta al JSON",
#     "output_dir": "ruta de salida",
#     "max_tasa_rechazo_pct": 30.0   # falla si se supera este umbral
#   }
# La función debe lanzar un ValueError si tasa_rechazo > max_tasa_rechazo_pct.
# Retorna el reporte de calidad.

# TODO:
