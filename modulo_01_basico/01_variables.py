# =============================================================================
# MÓDULO 1 - LECCIÓN 1: Variables y Tipos de Datos
# =============================================================================
# En Python no se declara el tipo explícitamente.
# El tipo se infiere automáticamente del valor asignado.
#
# Tipos básicos:
#   int     -> números enteros          ej: 42
#   float   -> números decimales        ej: 3.14
#   str     -> texto                    ej: "hola"
#   bool    -> verdadero/falso          ej: True / False
#   None    -> ausencia de valor        ej: None
# =============================================================================


# --- SECCIÓN 1: Declaración básica ---

nombre = "Ana"
edad = 28
altura = 1.65
activo = True
sin_valor = None

print(type(nombre))    # <class 'str'>
print(type(edad))      # <class 'int'>
print(type(altura))    # <class 'float'>
print(type(activo))    # <class 'bool'>


# --- SECCIÓN 2: Conversión de tipos (casting) ---

numero_texto = "100"
numero_real = int(numero_texto)       # str -> int
precio_texto = "29.99"
precio = float(precio_texto)          # str -> float
codigo = str(42)                      # int -> str

print(numero_real + 1)    # 101
print(precio * 2)         # 59.98


# --- SECCIÓN 3: Múltiples asignaciones ---

x = y = z = 0              # las tres valen 0
a, b, c = 1, 2, 3          # asignación en paralelo
print(a, b, c)             # 1 2 3


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# Declara las siguientes variables para representar un registro de ventas:
#   - nombre del producto (string)
#   - cantidad vendida (entero)
#   - precio unitario (decimal)
#   - si el producto está en stock (booleano)
# Luego imprime el tipo de cada una con type().

# TODO: escribe tu código aquí


# EJ-2
# Tienes este dato de una fuente externa (siempre llega como string):
#   registro = "2024"
# Conviértelo a entero, súmale 1 y guárdalo en una variable llamada `anio_siguiente`.
# Imprime el resultado.

registro = "2024"
# TODO: escribe tu código aquí


# EJ-3
# Contexto datos: en un pipeline ETL recibes estos valores como strings.
# Conviértelos al tipo correcto y calcula el ingreso total (cantidad * precio).
#
#   cantidad_str = "150"
#   precio_str = "49.90"
#   activo_str = "True"

cantidad_str = "150"
precio_str = "49.90"
activo_str = "True"
# TODO: convierte los tipos y calcula ingreso_total
# PISTA: bool("True") siempre es True — para convertir strings a bool
#        usa: activo = cantidad_str == "True" ... o compara directamente.


# EJ-4
# Usa asignación en paralelo para intercambiar los valores de a y b
# sin usar una variable temporal extra.
a = 10
b = 20
# TODO: intercambia a y b en una sola línea
print(a, b)    # debe imprimir: 20 10
