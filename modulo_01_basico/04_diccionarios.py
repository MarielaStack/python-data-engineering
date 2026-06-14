# =============================================================================
# MÓDULO 1 - LECCIÓN 4: Diccionarios
# =============================================================================
# Un diccionario almacena pares clave:valor.
# Las claves son únicas e inmutables (strings, números, tuplas).
# Los valores pueden ser cualquier tipo, incluyendo otros dicts o listas.
#
# En datos: representan filas (columna -> valor), configs de pipelines,
#           esquemas de tablas, resultados de APIs (JSON).
# =============================================================================


# --- SECCIÓN 1: Crear y acceder ---

producto = {
    "id": 101,
    "nombre": "arroz",
    "precio": 12.50,
    "activo": True,
}

print(producto["nombre"])          # arroz
print(producto.get("precio"))      # 12.50
print(producto.get("stock", 0))    # 0  (default si la clave no existe)


# --- SECCIÓN 2: Modificar ---

producto["precio"] = 13.00         # actualizar valor
producto["stock"] = 500            # agregar nueva clave
del producto["activo"]             # eliminar clave

# setdefault: asigna solo si la clave NO existe
producto.setdefault("categoria", "granos")
producto.setdefault("precio", 999)  # no hace nada, ya existe
print(producto)


# --- SECCIÓN 3: Métodos clave ---

config = {"host": "localhost", "puerto": 5432, "db": "ventas"}

print(config.keys())              # dict_keys(['host', 'puerto', 'db'])
print(config.values())            # dict_values(['localhost', 5432, 'ventas'])
print(config.items())             # lista de tuplas (clave, valor)

# iterar
for clave, valor in config.items():
    print(f"  {clave}: {valor}")

# combinar dos diccionarios (Python 3.9+ usa |, o usa update())
extra = {"timeout": 30, "puerto": 5433}   # 'puerto' sobreescribirá
config.update(extra)
print(config)


# --- SECCIÓN 4: Dicts anidados y listas de dicts ---

# Lista de dicts = tabla en memoria (patrón muy común en ETL)
tabla = [
    {"id": 1, "producto": "leche",  "cantidad": 100, "region": "norte"},
    {"id": 2, "producto": "arroz",  "cantidad": 200, "region": "sur"},
    {"id": 3, "producto": "aceite", "cantidad": 80,  "region": "norte"},
]

# acceder al segundo registro
print(tabla[1]["producto"])        # arroz

# dict comprehension
nombres = {fila["id"]: fila["producto"] for fila in tabla}
print(nombres)   # {1: 'leche', 2: 'arroz', 3: 'aceite'}


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# Tienes la configuración de una conexión a base de datos.
# Accede de forma segura a cada campo (usa .get con default apropiado
# si la clave podría no existir).
# Imprime una cadena de conexión con f-string:
#   "postgresql://usuario:contraseña@host:puerto/base_datos"

conexion = {
    "host": "db.empresa.com",
    "puerto": 5432,
    "base_datos": "dw_produccion",
    "usuario": "etl_user",
    "contrasena": "s3cret",
}
# TODO:


# EJ-2
# Dada la siguiente lista de registros de ventas (lista de dicts),
# calcula el total vendido por región usando un diccionario acumulador.
# Resultado esperado: {'norte': 2800, 'sur': 1500, 'este': 900}

ventas = [
    {"region": "norte", "monto": 1200},
    {"region": "sur",   "monto": 800},
    {"region": "norte", "monto": 1600},
    {"region": "este",  "monto": 900},
    {"region": "sur",   "monto": 700},
]
totales_por_region = {}
# TODO: recorre ventas y acumula en totales_por_region
# PISTA: usa .get(clave, 0) para sumar aunque la clave no exista aún.


# EJ-3
# Normaliza los nombres de las claves de este dict usando dict comprehension:
# strip + lower + replace espacios por guion bajo.
# Resultado esperado: {'id_cliente': 1, 'nombre': 'juan', 'monto_venta': 500.0}

fila_raw = {"  ID Cliente": 1, "Nombre": "juan", "MONTO VENTA": 500.0}
# TODO: fila_limpia = {... : ... for ...}


# EJ-4
# Merge de dos esquemas de tabla. Si una clave existe en ambos, conserva
# el tipo del esquema_nuevo (tiene prioridad).

esquema_viejo = {"id": "int", "nombre": "str", "precio": "float"}
esquema_nuevo = {"precio": "decimal", "stock": "int", "activo": "bool"}
# TODO: esquema_final = ...
# Resultado esperado: {'id': 'int', 'nombre': 'str', 'precio': 'decimal',
#                      'stock': 'int', 'activo': 'bool'}


# EJ-5 (desafío)
# Invierte el siguiente diccionario (clave <-> valor).
# Si hay valores repetidos, el último en iteración gana.
# Luego imprime qué columna tiene el tipo "str".

tipos_columnas = {
    "id": "int",
    "nombre": "str",
    "apellido": "str",
    "monto": "float",
    "fecha": "date",
}
# TODO: columnas_por_tipo = {...}
# Resultado esperado (aproximado): {'int': 'id', 'str': 'apellido', ...}
