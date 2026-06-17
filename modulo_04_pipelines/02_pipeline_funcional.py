# =============================================================================
# MÓDULO 4 - LECCIÓN 2: Pipeline Funcional
# =============================================================================
# El estilo funcional trata las transformaciones como funciones puras:
#   - Sin efectos secundarios
#   - Misma entrada -> siempre misma salida
#   - No modifican el estado global
#
# Herramientas:
#   pipe()          -> encadenar funciones sobre un valor
#   compose()       -> combinar funciones en una nueva función
#   functools.partial -> fijar argumentos de una función
#   map / filter    -> transformar y filtrar colecciones
#   functools.reduce -> acumular una colección en un valor
# =============================================================================

import functools
from typing import Callable, TypeVar

T = TypeVar("T")


# =============================================================================
# PARTE A — pipe: aplicar funciones en secuencia
# =============================================================================

# --- SECCIÓN 1: pipe() desde cero ---

def pipe(valor, *funciones):
    """
    Aplica cada función en orden sobre el valor.
    pipe(x, f, g, h)  ==  h(g(f(x)))
    """
    for fn in funciones:
        valor = fn(valor)
    return valor


# Ejemplo: limpiar un string de columna
resultado = pipe(
    "  MONTO VENTA  ",
    str.strip,
    str.lower,
    lambda s: s.replace(" ", "_"),
)
print(resultado)   # monto_venta


# Ejemplo: pipeline sobre lista de dicts
datos = [
    {"nombre": "  JUAN  ", "monto": 150.0, "region": "Norte"},
    {"nombre": "maria",    "monto": -20.0, "region": "SUR"},
    {"nombre": "PEDRO",    "monto": 300.0, "region": "este"},
]

def normalizar(registros):
    return [
        {**r, "nombre": r["nombre"].strip().title(),
              "region": r["region"].strip().lower()}
        for r in registros
    ]

def filtrar_positivos(registros):
    return [r for r in registros if r["monto"] > 0]

def agregar_categoria(registros):
    return [
        {**r, "categoria": "premium" if r["monto"] >= 200 else "normal"}
        for r in registros
    ]

resultado = pipe(datos, normalizar, filtrar_positivos, agregar_categoria)
for r in resultado:
    print(r)


# =============================================================================
# PARTE B — compose: crear una función desde varias
# =============================================================================

# --- SECCIÓN 2: compose() ---
# compose(f, g, h)(x)  ==  f(g(h(x)))  — orden inverso al de pipe

def compose(*funciones):
    """
    Combina funciones de derecha a izquierda.
    La última función se aplica primero.
    """
    def compuesta(valor):
        for fn in reversed(funciones):
            valor = fn(valor)
        return valor
    return compuesta


limpiar_columna = compose(
    lambda s: s.replace(" ", "_"),
    str.lower,
    str.strip,
)

print(limpiar_columna("  NOMBRE CLIENTE  "))   # nombre_cliente
print(limpiar_columna("  MONTO VENTA  "))      # monto_venta

# Útil para transformar esquemas de columnas
columnas_raw = ["  ID Cliente", "NOMBRE PROD", "MONTO VENTA", "  Fecha Orden  "]
columnas_limpias = list(map(limpiar_columna, columnas_raw))
print(columnas_limpias)


# =============================================================================
# PARTE C — functools.partial: funciones especializadas
# =============================================================================

# --- SECCIÓN 3: partial ---
# partial fija algunos argumentos de una función,
# creando una nueva función con menos parámetros.

def filtrar_por_campo(registros: list, campo: str, valor) -> list:
    return [r for r in registros if r.get(campo) == valor]

def agregar_columna(registros: list, nombre: str, fn: Callable) -> list:
    return [{**r, nombre: fn(r)} for r in registros]


# Crear versiones especializadas con partial
filtrar_norte  = functools.partial(filtrar_por_campo, campo="region", valor="norte")
filtrar_sur    = functools.partial(filtrar_por_campo, campo="region", valor="sur")
agregar_total  = functools.partial(
    agregar_columna,
    nombre="total",
    fn=lambda r: round(r["cantidad"] * r["precio"], 2)
)

ventas = [
    {"id": 1, "region": "norte", "cantidad": 100, "precio": 12.5},
    {"id": 2, "region": "sur",   "cantidad": 200, "precio": 8.0},
    {"id": 3, "region": "norte", "cantidad": 80,  "precio": 25.0},
]

print(filtrar_norte(ventas))
print(agregar_total(ventas))

# Componer con pipe usando funciones parciales
resultado = pipe(
    ventas,
    agregar_total,
    filtrar_norte,
)
print(resultado)


# =============================================================================
# PARTE D — map, filter, reduce
# =============================================================================

# --- SECCIÓN 4: map / filter / reduce ---

montos = [100.0, -50.0, 200.0, 0.0, 150.0, -10.0, 300.0]

# map: transformar cada elemento
con_iva     = list(map(lambda m: round(m * 1.16, 2), montos))

# filter: seleccionar elementos
positivos   = list(filter(lambda m: m > 0, montos))

# reduce: acumular
total       = functools.reduce(lambda acc, m: acc + m, positivos, 0.0)

print(f"Con IVA:    {con_iva}")
print(f"Positivos:  {positivos}")
print(f"Total:      {total}")

# Encadenar con pipe
total_positivos_con_iva = pipe(
    montos,
    lambda lst: filter(lambda m: m > 0, lst),
    lambda it:  map(lambda m: m * 1.16, it),
    lambda it:  functools.reduce(lambda a, b: a + b, it, 0.0),
    lambda t:   round(t, 2),
)
print(f"Total positivos + IVA: {total_positivos_con_iva}")


# =============================================================================
# PARTE E — Funciones de transformación reutilizables (librería de pasos)
# =============================================================================

# --- SECCIÓN 5: biblioteca de transformaciones ---
# Patrón real: defines una librería de pasos genéricos y los compones
# según el pipeline que necesitas.

def seleccionar(*campos):
    """Retorna solo los campos especificados de cada registro."""
    return lambda registros: [
        {k: r[k] for k in campos if k in r}
        for r in registros
    ]

def renombrar(**mapeo):
    """Renombra columnas. renombrar(viejo="nuevo")"""
    return lambda registros: [
        {mapeo.get(k, k): v for k, v in r.items()}
        for r in registros
    ]

def filtrar(condicion: Callable) -> Callable:
    """Filtra registros que cumplen la condición."""
    return lambda registros: [r for r in registros if condicion(r)]

def transformar_campo(campo: str, fn: Callable) -> Callable:
    """Aplica fn al campo especificado de cada registro."""
    return lambda registros: [{**r, campo: fn(r[campo])} for r in registros]

def agregar_campo(nombre: str, fn: Callable) -> Callable:
    """Agrega una columna calculada a cada registro."""
    return lambda registros: [{**r, nombre: fn(r)} for r in registros]


# Construir un pipeline con la librería
ventas_full = [
    {"id": 1, "producto": "arroz",  "region": "norte", "cantidad": 100, "precio": 12.5,  "activo": True},
    {"id": 2, "producto": "leche",  "region": "sur",   "cantidad": 200, "precio": 8.0,   "activo": False},
    {"id": 3, "producto": "aceite", "region": "norte", "cantidad": 80,  "precio": 25.0,  "activo": True},
    {"id": 4, "producto": "azucar", "region": "este",  "cantidad": 150, "precio": 9.75,  "activo": True},
]

resultado = pipe(
    ventas_full,
    filtrar(lambda r: r["activo"]),
    agregar_campo("total", lambda r: round(r["cantidad"] * r["precio"], 2)),
    filtrar(lambda r: r["total"] > 1000),
    seleccionar("id", "producto", "region", "total"),
    renombrar(producto="item", region="zona"),
)

print("\nResultado del pipeline funcional:")
for r in resultado:
    print(f"  {r}")


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# Usa pipe() para limpiar cada columna de este esquema de tabla.
# Cada clave del dict es un nombre de columna crudo.
# Resultado esperado: todas las claves en snake_case minúsculas sin espacios.
# Imprime el dict transformado.

esquema_raw = {
    "  ID Cliente ": "int",
    "NOMBRE PRODUCTO": "str",
    "Monto Venta": "float",
    "  FECHA ORDEN  ": "date",
    "Region": "str",
}
# TODO:


# EJ-2
# Crea una "librería" de 3 pasos reutilizables usando partial o closures:
#   - filtrar_region(region)   -> filtra registros por esa región
#   - top_n(n, campo)          -> devuelve los n registros con mayor valor en campo
#   - redondear(campo, decimales) -> redondea el campo a N decimales
# Luego construye un pipeline con pipe() que:
#   1. Filtre region="norte"
#   2. Agregue campo "total" = cantidad * precio
#   3. Tome el top 2 por "total"
#   4. Redondee "total" a 1 decimal

# TODO:


# EJ-3
# Implementa compose() inverso — es decir, que aplique las funciones
# de izquierda a derecha (igual que pipe pero retorna una función).
# Llámalo pipeline_fn(*pasos) -> Callable.
# Úsalo para crear una función `limpiar_registro` que normalice
# nombre y región de un dict de ventas.

# TODO:


# EJ-4
# Usa map, filter y reduce para responder:
#   a) ¿Cuál es el total de ventas (cantidad * precio) de la región "norte"?
#   b) ¿Cuántos registros tienen monto > 1000?
#   c) ¿Cuál es el producto más vendido (mayor suma de cantidad)?
# Todo en expresiones de una sola línea con map/filter/reduce, sin for.

# TODO: trabaja sobre ventas_full


# EJ-5 (desafío)
# Implementa `pipeline_paralelo(datos, *ramas)` donde cada rama es una
# lista de pasos. Aplica todas las ramas sobre los mismos datos de entrada
# y retorna una lista con el resultado de cada rama.
# Pruébalo con 3 ramas distintas sobre ventas_full:
#   rama_1: norte con total
#   rama_2: activos ordenados por precio desc
#   rama_3: resumen {total_registros, suma_total}

# TODO:
