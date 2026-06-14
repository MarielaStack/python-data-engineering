# =============================================================================
# MÓDULO 2 - LECCIÓN 1: Manejo de Errores
# =============================================================================
# try / except / else / finally
# raise, excepciones personalizadas
#
# En datos: conexiones que fallan, archivos corruptos, tipos inesperados,
#           filas con valores inválidos — los errores son la norma, no la excepción.
# =============================================================================


# --- SECCIÓN 1: try / except básico ---

# Sin manejo de errores, esto rompe el programa:
# print(int("abc"))   # ValueError

# Con manejo:
texto = "abc"
try:
    numero = int(texto)
except ValueError:
    print(f"No se puede convertir '{texto}' a entero")


# --- SECCIÓN 2: Capturar múltiples excepciones ---

def parsear_monto(valor) -> float:
    try:
        return float(valor)
    except (ValueError, TypeError) as e:
        print(f"  Error parseando '{valor}': {e}")
        return 0.0

print(parsear_monto("29.90"))    # 29.9
print(parsear_monto("abc"))      # Error + 0.0
print(parsear_monto(None))       # Error + 0.0


# --- SECCIÓN 3: else y finally ---

# else   -> se ejecuta si NO hubo excepción
# finally -> se ejecuta SIEMPRE (con o sin error) — ideal para cerrar recursos

def leer_archivo(ruta: str):
    archivo = None
    try:
        archivo = open(ruta, "r")
        contenido = archivo.read()
    except FileNotFoundError:
        print(f"Archivo no encontrado: {ruta}")
        return None
    else:
        print(f"Archivo leído: {len(contenido)} caracteres")
        return contenido
    finally:
        if archivo:
            archivo.close()
            print("Archivo cerrado")

leer_archivo("no_existe.csv")


# --- SECCIÓN 4: raise — lanzar errores intencionalmente ---

def dividir(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("El divisor no puede ser cero")
    return a / b

try:
    print(dividir(10, 0))
except ValueError as e:
    print(f"Error: {e}")


# --- SECCIÓN 5: Excepciones personalizadas ---

class ErrorValidacion(Exception):
    """Se lanza cuando un registro no pasa validación."""
    def __init__(self, campo: str, motivo: str):
        self.campo = campo
        self.motivo = motivo
        super().__init__(f"Campo '{campo}': {motivo}")

class ErrorConexion(Exception):
    """Se lanza cuando falla la conexión a una fuente de datos."""
    pass


def validar_fila(fila: dict):
    if fila.get("id") is None:
        raise ErrorValidacion("id", "es obligatorio")
    if not isinstance(fila.get("monto"), (int, float)):
        raise ErrorValidacion("monto", "debe ser numérico")
    if fila["monto"] < 0:
        raise ErrorValidacion("monto", "no puede ser negativo")

try:
    validar_fila({"id": 1, "monto": -50})
except ErrorValidacion as e:
    print(f"Validación fallida — {e}")


# --- SECCIÓN 6: Procesar lista con errores sin detener el pipeline ---

registros = [
    {"id": 1, "monto": "150.0"},
    {"id": 2, "monto": "abc"},
    {"id": 3, "monto": "200.5"},
    {"id": None, "monto": "50.0"},
]

procesados = []
errores = []

for fila in registros:
    try:
        if fila["id"] is None:
            raise ErrorValidacion("id", "es obligatorio")
        fila["monto"] = float(fila["monto"])
        procesados.append(fila)
    except (ValueError, ErrorValidacion) as e:
        errores.append({"fila": fila, "error": str(e)})

print(f"\nProcesados: {len(procesados)}, Errores: {len(errores)}")
for err in errores:
    print(f"  {err}")


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# Escribe una función `convertir_tipos(fila: dict) -> dict` que convierta
# los valores del dict al tipo correcto según este esquema:
#   {"id": int, "nombre": str, "precio": float, "activo": bool}
# Si alguna conversión falla, lanza un ValueError con el nombre del campo.
# Prueba con:
#   fila_ok  = {"id": "5", "nombre": "arroz", "precio": "12.5", "activo": "True"}
#   fila_err = {"id": "abc", "nombre": "leche", "precio": "8.0", "activo": "False"}

esquema = {"id": int, "nombre": str, "precio": float}
# TODO: def convertir_tipos(fila: dict) -> dict: ...


# EJ-2
# Implementa `cargar_con_reintentos(url: str, max_intentos: int = 3)`.
# Simula una carga que falla las primeras 2 veces (usa una variable externa
# `llamadas = 0` que incrementas dentro) y tiene éxito en el 3er intento.
# En cada intento imprime el número. Si se agotan los intentos,
# lanza un ErrorConexion con el mensaje apropiado.

llamadas = 0
# TODO: def cargar_con_reintentos(url, max_intentos=3): ...


# EJ-3
# Crea una clase de excepción `ErrorETL` con atributos:
#   etapa: str    ("extraccion", "transformacion", "carga")
#   detalle: str
# y __str__ que imprima: "[ETL-etapa] detalle"
#
# Luego escribe una función `ejecutar_etapa(etapa: str, datos: list)`
# que si datos está vacío lanza ErrorETL("transformacion", "sin datos").

# TODO:


# EJ-4
# Procesa la siguiente lista de filas crudas.
# Cada fila viene con valores string. Intenta:
#   1. Convertir 'cantidad' a int
#   2. Convertir 'precio' a float
#   3. Calcular 'total' = cantidad * precio
# Acumula las filas exitosas en `ok` y los errores en `fallos` (con motivo).
# Al final imprime resumen.

filas_crudas = [
    {"producto": "arroz",  "cantidad": "100", "precio": "12.50"},
    {"producto": "leche",  "cantidad": "cincuenta", "precio": "8.00"},
    {"producto": "aceite", "cantidad": "80",  "precio": "N/A"},
    {"producto": "azucar", "cantidad": "200", "precio": "9.75"},
    {"producto": "sal",    "cantidad": "150", "precio": "3.00"},
]
ok = []
fallos = []
# TODO:


# EJ-5 (desafío)
# Escribe un decorador `capturar_errores` que envuelva cualquier función
# y, si lanza una excepción, la imprime y retorna None en lugar de propagar.
#
# Úsalo así:
#   @capturar_errores
#   def dividir_seguro(a, b):
#       return a / b
#
#   print(dividir_seguro(10, 2))    # 5.0
#   print(dividir_seguro(10, 0))    # imprime el error, retorna None

# TODO: def capturar_errores(func): ...
