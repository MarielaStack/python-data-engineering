# =============================================================================
# MÓDULO 1 - LECCIÓN 2: Strings y Formateo
# =============================================================================
# Un string es una cadena de texto inmutable.
# Python ofrece varios métodos para manipularlos y tres formas de formateo.
# =============================================================================


# --- SECCIÓN 1: Métodos de strings más usados ---

texto = "  Hola Mundo  "

print(texto.strip())          # elimina espacios al inicio y fin -> "Hola Mundo"
print(texto.lower())          # todo en minúsculas
print(texto.upper())          # todo en mayúsculas
print(texto.replace("Mundo", "Python"))   # reemplaza

ciudad = "La Paz"
print(ciudad.startswith("La"))   # True
print(ciudad.endswith("z"))      # True
print(len(ciudad))               # 6  (cantidad de caracteres)

csv_line = "2024-01-15,ventas,1500.50,activo"
partes = csv_line.split(",")     # divide por separador -> lista
print(partes)                    # ['2024-01-15', 'ventas', '1500.50', 'activo']


# --- SECCIÓN 2: Indexación y slicing ---

texto = "pipeline"
#         01234567

print(texto[0])       # 'p'  (primer carácter)
print(texto[-1])      # 'e'  (último carácter)
print(texto[0:4])     # 'pipe' (desde índice 0 hasta 3, el 4 no se incluye)
print(texto[4:])      # 'line' (desde índice 4 hasta el final)
print(texto[::-1])    # 'enilepip' (string invertido)


# --- SECCIÓN 3: Tres formas de formateo ---

producto = "arroz"
cantidad = 150
precio = 29.90

# Opción A — % (antigua, evitar)
print("Producto: %s, Cant: %d, Precio: %.2f" % (producto, cantidad, precio))

# Opción B — .format()
print("Producto: {}, Cant: {}, Precio: {:.2f}".format(producto, cantidad, precio))

# Opción C — f-string (recomendada, Python 3.6+)
print(f"Producto: {producto}, Cant: {cantidad}, Precio: {precio:.2f}")

# f-strings pueden ejecutar expresiones
print(f"Total: {cantidad * precio:.2f}")
print(f"Producto en mayúsculas: {producto.upper()}")


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# Tienes el nombre de una columna con espacios y mayúsculas inconsistentes.
# Limpiarlo es una tarea común en ETL.
#   columna_raw = "  Nombre Cliente  "
# Normalízala: sin espacios al inicio/fin, todo en minúsculas, espacios
# internos reemplazados por guion bajo. Resultado esperado: "nombre_cliente"

columna_raw = "  Nombre Cliente  "
# TODO:


# EJ-2
# Tienes esta línea de un archivo de log de un pipeline:
#   log_line = "2024-03-10|ERROR|pipeline_ventas|Timeout al conectar con BD"
# Usa split() para extraer:
#   fecha, nivel, pipeline, mensaje
# e imprime cada parte en su propia línea con f-strings.

log_line = "2024-03-10|ERROR|pipeline_ventas|Timeout al conectar con BD"
# TODO:


# EJ-3
# Dado un nombre de tabla con formato crudo, genera el nombre del archivo
# de salida con este formato: "export_NOMBRETABLA_2024.csv"
#   tabla = "  Ordenes De Compra  "
# Resultado esperado: "export_ordenes_de_compra_2024.csv"

tabla = "  Ordenes De Compra  "
# TODO:


# EJ-4
# Usa slicing para extraer el año y el mes de esta fecha en formato string.
#   fecha = "2024-07-22"
# Guárdalos en variables `anio` y `mes` (como strings).
# Imprime: "Año: 2024 | Mes: 07"

fecha = "2024-07-22"
# TODO:


# EJ-5 (desafío)
# Verifica si un nombre de columna es válido para usar en SQL.
# Una columna es válida si:
#   1. No tiene espacios
#   2. Está en minúsculas
#   3. No empieza con un número
# Usa métodos de string para construir los tres checks e imprime
# True/False para cada condición.

columna = "ventas_2024"
# TODO:
