# =============================================================================
# MÓDULO 1 - LECCIÓN 7: Funciones
# =============================================================================
# Una función agrupa código reutilizable bajo un nombre.
# En datos: transformaciones, validaciones, parsers, extractores.
#
# Conceptos:
#   - parámetros posicionales y con valor por defecto
#   - *args y **kwargs
#   - type hints (anotaciones de tipo)
#   - retorno múltiple (tuplas)
#   - funciones lambda
# =============================================================================


# --- SECCIÓN 1: Definición básica ---

def saludar(nombre: str) -> str:
    return f"Hola, {nombre}!"

print(saludar("Ana"))


# --- SECCIÓN 2: Parámetros con defaults y keyword args ---

def crear_conexion(host: str, puerto: int = 5432, db: str = "default") -> str:
    return f"{host}:{puerto}/{db}"

print(crear_conexion("localhost"))                          # usa defaults
print(crear_conexion("db.prod.com", db="ventas"))          # keyword arg
print(crear_conexion("db.prod.com", 5433, "reportes"))     # posicional


# --- SECCIÓN 3: Retorno múltiple ---

def estadisticas(valores: list) -> tuple:
    total = sum(valores)
    promedio = total / len(valores)
    maximo = max(valores)
    minimo = min(valores)
    return total, promedio, maximo, minimo

total, promedio, maximo, minimo = estadisticas([100, 200, 300, 400])
print(f"Total={total}, Prom={promedio}, Max={maximo}, Min={minimo}")


# --- SECCIÓN 4: *args y **kwargs ---

def suma_todos(*numeros: float) -> float:
    """Acepta cualquier cantidad de argumentos posicionales."""
    return sum(numeros)

print(suma_todos(1, 2, 3, 4, 5))    # 15

def log_evento(nivel: str, mensaje: str, **contexto) -> None:
    """Acepta campos extras arbitrarios para el log."""
    detalles = ", ".join(f"{k}={v}" for k, v in contexto.items())
    print(f"[{nivel}] {mensaje} | {detalles}")

log_evento("INFO", "Pipeline completado", pipeline="ventas", filas=1500)
log_evento("ERROR", "Fallo en carga", tabla="ordenes", codigo=500)


# --- SECCIÓN 5: Funciones lambda ---

# lambda es una función anónima de una sola expresión.
# Útil para usar como argumento (sorted, map, filter).

normalizar = lambda s: s.strip().lower().replace(" ", "_")
print(normalizar("  NOMBRE CLIENTE  "))   # nombre_cliente

registros = [{"nombre": "arroz", "precio": 12.5},
             {"nombre": "leche", "precio": 8.0},
             {"nombre": "aceite", "precio": 25.0}]

# ordenar por precio de mayor a menor
ordenados = sorted(registros, key=lambda r: r["precio"], reverse=True)
for r in ordenados:
    print(f"  {r['nombre']}: {r['precio']}")


# --- SECCIÓN 6: Funciones como argumentos (map / filter) ---

montos = [100, -50, 200, -30, 400]

montos_limpios = list(filter(lambda m: m > 0, montos))        # [100, 200, 400]
montos_con_iva = list(map(lambda m: round(m * 1.16, 2), montos_limpios))

print(montos_limpios)
print(montos_con_iva)


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# Escribe una función `normalizar_columna(nombre: str) -> str` que:
#   1. Elimine espacios al inicio/fin
#   2. Convierta a minúsculas
#   3. Reemplace espacios internos por guion bajo
# Pruébala con: "  MONTO VENTA  " -> "monto_venta"

# TODO:


# EJ-2
# Escribe una función `calcular_metricas(ventas: list) -> dict` que reciba
# una lista de montos y retorne un diccionario con:
#   {"total": ..., "promedio": ..., "maximo": ..., "minimo": ..., "conteo": ...}
# Maneja el caso de lista vacía retornando None.

# TODO:
ventas = [1200.0, 850.5, 2100.0, 975.0, 1340.0]
# print(calcular_metricas(ventas))
# print(calcular_metricas([]))


# EJ-3
# Escribe una función `parsear_fecha(fecha_str: str, separador: str = "-") -> dict`
# que reciba una fecha en formato "YYYY-MM-DD" (o con otro separador)
# y retorne {"anio": int, "mes": int, "dia": int}.
# Si el formato es inválido retorna None.

# TODO:
# print(parsear_fecha("2024-03-15"))           # {"anio": 2024, "mes": 3, "dia": 15}
# print(parsear_fecha("15/03/2024", "/"))      # {"anio": 2024, "mes": 3, "dia": 15} — OJO orden
# print(parsear_fecha("fecha-invalida"))       # None


# EJ-4
# Escribe `log_pipeline(**kwargs)` que acepte campos arbitrarios y los imprima
# en formato clave=valor separados por " | ".
# Ejemplo de llamada:
#   log_pipeline(pipeline="ventas", estado="OK", filas=1500, duracion_seg=12.3)
# Salida:
#   pipeline=ventas | estado=OK | filas=1500 | duracion_seg=12.3

# TODO:


# EJ-5 (desafío)
# Implementa una función `aplicar_pipeline(datos: list, *transformaciones) -> list`
# que reciba una lista de strings y una cantidad variable de funciones,
# y aplique cada función en orden sobre cada elemento.
#
# Luego pruébala con estas transformaciones:
#   - strip
#   - str.lower
#   - lambda s: s.replace(" ", "_")
#
# Entrada:  ["  NOMBRE CLIENTE  ", "CIUDAD ORIGEN", " TIPO PRODUCTO "]
# Salida:   ["nombre_cliente", "ciudad_origen", "tipo_producto"]

# TODO:
