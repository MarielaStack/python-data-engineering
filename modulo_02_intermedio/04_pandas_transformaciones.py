# =============================================================================
# MÓDULO 2 - LECCIÓN 4: Pandas — Transformaciones
# =============================================================================
# Filtros, ordenamiento, groupby, merge, apply, pivot
# Estas operaciones cubren el 80% de las transformaciones en pipelines reales.
# =============================================================================

import pandas as pd
import numpy as np

# Dataset base: ventas con regiones y fechas
ventas = pd.DataFrame({
    "id":       [1, 2, 3, 4, 5, 6, 7, 8],
    "fecha":    ["2024-01-10", "2024-01-15", "2024-02-05",
                 "2024-02-20", "2024-03-01", "2024-03-15", "2024-01-22", "2024-03-28"],
    "producto": ["arroz", "leche", "arroz", "aceite", "leche", "arroz", "azucar", "aceite"],
    "region":   ["norte", "sur", "norte", "este", "sur", "norte", "este", "sur"],
    "cantidad": [100, 200, 80, 60, 150, 120, 90, 70],
    "precio":   [12.50, 8.00, 12.50, 25.00, 8.00, 12.50, 9.75, 25.00],
})
ventas["total"] = ventas["cantidad"] * ventas["precio"]
ventas["fecha"] = pd.to_datetime(ventas["fecha"])

print(ventas.to_string())
print()


# =============================================================================
# PARTE A — Filtros
# =============================================================================

# Filtro simple
norte = ventas[ventas["region"] == "norte"]
print(f"Ventas norte: {len(norte)} filas")

# Filtro con múltiples condiciones (& = AND, | = OR, ~ = NOT)
caros_norte = ventas[(ventas["region"] == "norte") & (ventas["precio"] > 10)]
print(f"Caros en norte: {len(caros_norte)} filas")

# .query() — sintaxis más legible
resultado = ventas.query("region == 'sur' and total > 1000")
print(result := resultado[["producto", "region", "total"]])

# isin — equivalente a IN de SQL
productos_key = ventas[ventas["producto"].isin(["arroz", "aceite"])]
print(f"Productos clave: {len(productos_key)} filas")

# between
ventas_medias = ventas[ventas["total"].between(500, 2000)]
print(f"Ventas entre 500 y 2000: {len(ventas_medias)}")

# Filtrar nulos
ventas_copy = ventas.copy()
ventas_copy.loc[2, "precio"] = None          # simular nulo
sin_nulos  = ventas_copy[ventas_copy["precio"].notna()]
solo_nulos = ventas_copy[ventas_copy["precio"].isna()]
print(f"Sin nulos: {len(sin_nulos)}, Solo nulos: {len(solo_nulos)}")


# =============================================================================
# PARTE B — Ordenamiento y selección
# =============================================================================

por_total = ventas.sort_values("total", ascending=False)
print(por_total[["producto", "region", "total"]].head(3))

# top 3 por región (primero ordena, luego toma head por grupo)
top_region = (ventas
    .sort_values("total", ascending=False)
    .groupby("region")
    .head(2))
print(top_region[["region", "producto", "total"]])


# =============================================================================
# PARTE C — groupby
# =============================================================================

# Total y conteo por región
por_region = ventas.groupby("region").agg(
    total_ventas=("total", "sum"),
    num_transacciones=("id", "count"),
    precio_promedio=("precio", "mean"),
).round(2).reset_index()

print(por_region)

# Múltiples columnas de agrupación
por_region_producto = ventas.groupby(["region", "producto"])["total"].sum().reset_index()
print(por_region_producto)

# transform: agrega la métrica del grupo de vuelta a cada fila
ventas["total_region"] = ventas.groupby("region")["total"].transform("sum")
ventas["pct_region"]   = (ventas["total"] / ventas["total_region"] * 100).round(1)
print(ventas[["producto", "region", "total", "pct_region"]])


# =============================================================================
# PARTE D — merge (JOIN)
# =============================================================================

# Tabla de productos
productos_df = pd.DataFrame({
    "producto":   ["arroz", "leche", "aceite", "azucar", "sal"],
    "categoria":  ["granos", "lacteo", "aceite", "dulce", "condimento"],
    "proveedor":  ["ProvA", "ProvB", "ProvA", "ProvC", "ProvC"],
})

# INNER JOIN (solo coincidencias)
enriquecido = ventas.merge(productos_df, on="producto", how="inner")
print(enriquecido[["producto", "categoria", "proveedor", "total"]].head())

# LEFT JOIN (todas las filas de ventas, NaN si no hay match)
ventas_all = ventas.merge(productos_df, on="producto", how="left")

# Merge por múltiples columnas
ventas2 = ventas.copy()
ventas2["anio"] = ventas2["fecha"].dt.year
metas = pd.DataFrame({"region": ["norte", "sur", "este"], "meta": [5000, 4000, 3000]})
con_meta = ventas2.merge(metas, on="region", how="left")
print(con_meta[["region", "total", "meta"]].head())


# =============================================================================
# PARTE E — apply y map
# =============================================================================

# apply: aplica una función a cada elemento/fila
ventas["clasificacion"] = ventas["total"].apply(
    lambda t: "alto" if t >= 2000 else "medio" if t >= 1000 else "bajo"
)

# apply sobre filas (axis=1) — accede a varias columnas
ventas["resumen"] = ventas.apply(
    lambda row: f"{row['producto']} ({row['region']}): {row['total']:.0f}",
    axis=1
)
print(ventas["resumen"].head())

# map en Series — reemplaza valores según un dict
mapa_region = {"norte": "N", "sur": "S", "este": "E"}
ventas["region_cod"] = ventas["region"].map(mapa_region)
print(ventas[["region", "region_cod"]].drop_duplicates())


# =============================================================================
# PARTE F — Fechas
# =============================================================================

ventas["anio"]  = ventas["fecha"].dt.year
ventas["mes"]   = ventas["fecha"].dt.month
ventas["dia"]   = ventas["fecha"].dt.day
ventas["trim"]  = ventas["fecha"].dt.quarter

ventas_por_mes = ventas.groupby(["anio", "mes"])["total"].sum().reset_index()
print(ventas_por_mes)


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# Del DataFrame ventas filtra:
#   a) Todas las ventas del mes de enero
#   b) Ventas con total > 1500 Y producto != "arroz"
#   c) Ventas cuyo producto empiece con "a" (usa .str.startswith())

# TODO:


# EJ-2
# Con groupby, calcula para cada producto:
#   - suma de cantidad vendida
#   - suma de total
#   - precio promedio
#   - número de ventas
# Ordena de mayor a menor por total. Guarda en un DataFrame `resumen_productos`.

# TODO:


# EJ-3
# Tienes esta tabla de objetivos por región:
objetivos = pd.DataFrame({
    "region":   ["norte", "sur", "este"],
    "objetivo": [4000.0, 3500.0, 2500.0],
})
# Haz un LEFT JOIN con ventas (agrupado por región) para ver si cada región
# alcanzó su objetivo. Agrega una columna "cumplido" (bool) y "diferencia".

# TODO:


# EJ-4
# Usa apply con axis=1 para crear una columna "alerta" que sea:
#   "descuento_alto" si cantidad > 100 y precio < 10
#   "margen_alto"    si precio > 20
#   "normal"         en otro caso

# TODO:


# EJ-5 (desafío)
# Crea un reporte mensual con groupby y fechas:
#   columnas: anio, mes, total_ventas, num_transacciones, producto_top (el de mayor total ese mes)
# PISTA: para producto_top puedes usar idxmax() dentro de un apply sobre el grupo.

# TODO:
