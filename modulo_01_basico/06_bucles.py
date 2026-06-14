# =============================================================================
# MÓDULO 1 - LECCIÓN 6: Bucles (for / while)
# =============================================================================
# for   -> iterar sobre una secuencia conocida (lista, dict, rango)
# while -> repetir mientras una condición sea verdadera
#
# En datos: procesar filas, leer archivos por lotes (batch), reintentos,
#           transformaciones sobre colecciones.
# =============================================================================


# --- SECCIÓN 1: for básico ---

frutas = ["pera", "manzana", "uva"]
for fruta in frutas:
    print(fruta)

# range(start, stop, step)
for i in range(5):              # 0 1 2 3 4
    print(i, end=" ")
print()

for i in range(0, 10, 2):      # 0 2 4 6 8
    print(i, end=" ")
print()


# --- SECCIÓN 2: enumerate y zip ---

columnas = ["id", "nombre", "precio"]
for indice, col in enumerate(columnas, start=1):
    print(f"  Col {indice}: {col}")

claves =  ["host",        "puerto", "db"]
valores = ["localhost",   5432,     "ventas"]
for k, v in zip(claves, valores):
    print(f"  {k} = {v}")

# Construir un dict con zip
config = dict(zip(claves, valores))
print(config)


# --- SECCIÓN 3: Iterar dicts ---

fila = {"id": 1, "producto": "arroz", "monto": 150.0}

for clave in fila:                      # itera solo claves
    print(clave)

for clave, valor in fila.items():       # claves Y valores
    print(f"  {clave}: {valor}")


# --- SECCIÓN 4: break, continue, else ---

precios = [10, -5, 30, -2, 50]
for precio in precios:
    if precio < 0:
        continue            # salta este elemento
    print(precio)

# break: detiene el bucle
for precio in precios:
    if precio < 0:
        print("Precio negativo encontrado, abortando")
        break

# else en for: se ejecuta si el bucle terminó SIN break
for precio in precios:
    if precio < 0:
        break
else:
    print("Todos los precios son válidos")   # no se imprime en este caso


# --- SECCIÓN 5: while ---

intentos = 0
max_intentos = 3
conectado = False

while intentos < max_intentos and not conectado:
    intentos += 1
    print(f"Intento {intentos} de conexión...")
    if intentos == 2:          # simula que conecta en el 2do intento
        conectado = True

if conectado:
    print("Conexión establecida")
else:
    print("No se pudo conectar")


# --- SECCIÓN 6: Procesamiento en lotes (batch) ---

registros = list(range(1, 26))   # 25 registros simulados
tamanio_lote = 10

for i in range(0, len(registros), tamanio_lote):
    lote = registros[i:i + tamanio_lote]
    print(f"Procesando lote {i // tamanio_lote + 1}: {lote}")


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# Itera la siguiente lista de ventas e imprime un resumen por fila:
#   "Venta #1: producto=arroz, region=norte, monto=1200.0"
# Usa enumerate para tener el número de venta.

ventas = [
    {"producto": "arroz",  "region": "norte", "monto": 1200.0},
    {"producto": "leche",  "region": "sur",   "monto": 850.0},
    {"producto": "aceite", "region": "norte", "monto": 2100.0},
]
# TODO:


# EJ-2
# Construye un diccionario de totales por producto a partir de la lista
# de ventas anterior. Resultado esperado:
#   {'arroz': 1200.0, 'leche': 850.0, 'aceite': 2100.0}
# (si hubiera repetidos, deberías sumar)

totales = {}
# TODO: usa un for para acumular
print(totales)


# EJ-3
# Implementa un procesador de lotes (batch processor).
# Tienes 100 registros simulados (usa range(1, 101)).
# Procésalos en lotes de 15 e imprime:
#   "Lote 1: registros 1 a 15"
#   "Lote 2: registros 16 a 30"
#   ...

# TODO:


# EJ-4
# Usa while para simular reintentos de conexión a una base de datos.
# Intenta conectar máximo 5 veces. Simula que la conexión falla las 3 primeras
# (usa una variable `intento` para decidir cuándo "conecta").
# Imprime el estado de cada intento y el resultado final.

# TODO:


# EJ-5 (desafío)
# Dado el siguiente pipeline de transformaciones, aplica cada función
# en secuencia sobre cada fila de datos usando un for anidado.
# El pipeline es una lista de funciones; aplica una por una a cada valor
# de la columna "nombre".

import re

def strip_espacios(v):
    return v.strip() if isinstance(v, str) else v

def a_minusculas(v):
    return v.lower() if isinstance(v, str) else v

def reemplazar_espacios(v):
    return re.sub(r"\s+", "_", v) if isinstance(v, str) else v

datos = [
    {"id": 1, "nombre": "  Juan Lopez  "},
    {"id": 2, "nombre": "MARIA GARCIA"},
    {"id": 3, "nombre": "pedro  alvarez"},
]
pipeline_fn = [strip_espacios, a_minusculas, reemplazar_espacios]

# TODO: aplica pipeline_fn a datos["nombre"] de cada fila y guarda el resultado
# en una nueva lista `datos_limpios` (puedes mutar el dict o crear copias)
# Resultado esperado nombres: ['juan_lopez', 'maria_garcia', 'pedro_alvarez']
