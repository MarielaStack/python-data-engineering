# =============================================================================
# MÓDULO 1 - LECCIÓN 3: Listas y Tuplas
# =============================================================================
# Lista  -> colección ordenada, MUTABLE   -> se puede modificar después de creada
# Tupla  -> colección ordenada, INMUTABLE -> no se puede modificar
#
# En ingeniería de datos:
#   listas  -> filas en memoria, columnas de un DataFrame, resultados de queries
#   tuplas  -> coordenadas, claves compuestas, registros que no deben cambiar
# =============================================================================


# --- SECCIÓN 1: Listas básicas ---

frutas = ["manzana", "banana", "pera"]
numeros = [10, 20, 30, 40, 50]
mixto = [1, "texto", True, 3.14]     # Python permite tipos mixtos (no recomendado en datos)

print(frutas[0])       # "manzana"
print(frutas[-1])      # "pera"
print(numeros[1:3])    # [20, 30]
print(len(frutas))     # 3


# --- SECCIÓN 2: Modificar listas ---

columnas = ["id", "nombre", "precio"]

columnas.append("fecha")               # agrega al final
columnas.insert(1, "codigo")           # inserta en posición 1
columnas.remove("nombre")              # elimina por valor
ultimo = columnas.pop()                # elimina y devuelve el último
print(columnas)

# ordenar
precios = [45.0, 12.5, 99.0, 30.0]
precios.sort()                         # modifica en lugar
print(precios)
print(sorted(precios, reverse=True))   # devuelve nueva lista ordenada desc


# --- SECCIÓN 3: Operaciones útiles ---

a = [1, 2, 3]
b = [4, 5, 6]
print(a + b)           # concatenar -> [1, 2, 3, 4, 5, 6]
print(a * 2)           # repetir    -> [1, 2, 3, 1, 2, 3]
print(3 in a)          # True (membership check)
print(sum(a))          # 6
print(max(b))          # 6
print(min(b))          # 4


# --- SECCIÓN 4: Tuplas ---

punto = (10, 20)
registro = ("2024-01-15", "ventas", 1500.0)

print(punto[0])        # 10
x, y = punto           # desempaquetado (unpacking)
fecha, area, monto = registro

# Las tuplas son hashables -> se pueden usar como llaves de diccionario
tabla_particion = {("2024", "enero"): 1200, ("2024", "febrero"): 1350}


# --- SECCIÓN 5: List comprehensions (intro) ---

numeros = [1, 2, 3, 4, 5]
cuadrados = [n ** 2 for n in numeros]           # [1, 4, 9, 16, 25]
pares = [n for n in numeros if n % 2 == 0]     # [2, 4]
print(cuadrados)
print(pares)


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# Tienes una lista de columnas de una tabla cruda.
# Algunas columnas tienen espacios y mayúsculas inconsistentes.
# Normaliza cada columna: strip + lower + replace(" ", "_")
# Usa una list comprehension.

columnas_raw = ["  ID Cliente", "Nombre ", "MONTO VENTA", "fecha orden  "]
# TODO: columnas_limpias = [...]
# Resultado esperado: ['id_cliente', 'nombre', 'monto_venta', 'fecha_orden']


# EJ-2
# Tienes los montos de ventas de una semana.
# Calcula: total, promedio, mínimo, máximo e imprime un resumen con f-strings.

ventas_semana = [1200.0, 850.5, 2100.0, 975.0, 1340.0, 600.0, 1800.0]
# TODO:


# EJ-3
# Filtra de la siguiente lista solo los registros con estado "activo"
# usando una list comprehension. Cada elemento es una tupla (id, estado).

registros = [
    (1, "activo"),
    (2, "inactivo"),
    (3, "activo"),
    (4, "pendiente"),
    (5, "activo"),
]
# TODO: activos = [...]
# Resultado esperado: [(1, 'activo'), (3, 'activo'), (5, 'activo')]


# EJ-4
# Combina dos listas de columnas eliminando duplicados.
# Mantén el orden: primero las de tabla_a, luego las nuevas de tabla_b.

tabla_a = ["id", "nombre", "precio", "fecha"]
tabla_b = ["id", "nombre", "categoria", "stock", "fecha"]
# TODO: columnas_unidas = [...]
# Resultado esperado: ['id', 'nombre', 'precio', 'fecha', 'categoria', 'stock']
# PISTA: recorre tabla_b y agrega solo si el elemento no está ya en la lista.


# EJ-5 (desafío)
# Dada una lista de precios con posibles valores None o negativos,
# construye una lista limpia que solo contenga valores positivos.
# Usa una list comprehension con condición.

precios_raw = [10.5, None, -5.0, 200.0, None, 0, 88.0, -1.0, 45.0]
# TODO: precios_limpios = [...]
# Resultado esperado: [10.5, 200.0, 88.0, 45.0]
