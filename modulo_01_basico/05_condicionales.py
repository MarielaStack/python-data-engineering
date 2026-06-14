# =============================================================================
# MÓDULO 1 - LECCIÓN 5: Condicionales
# =============================================================================
# if / elif / else controlan el flujo según condiciones.
# En datos: validación de registros, clasificación, lógica de negocio,
#           manejo de nulos, detección de anomalías.
# =============================================================================


# --- SECCIÓN 1: if / elif / else básico ---

temperatura = 37.5

if temperatura > 39:
    print("Fiebre alta")
elif temperatura > 37:
    print("Fiebre leve")
elif temperatura >= 36:
    print("Normal")
else:
    print("Hipotermia")


# --- SECCIÓN 2: Operadores de comparación y lógicos ---

# Comparación: ==  !=  >  <  >=  <=
# Lógicos:     and  or  not
# Identidad:   is  is not
# Pertenencia: in  not in

score = 85
categoria = "A" if score >= 90 else "B" if score >= 75 else "C"    # ternario
print(categoria)    # B

valor = None
if valor is None:
    print("El campo está vacío")

columnas_requeridas = ["id", "nombre", "fecha"]
if "id" in columnas_requeridas:
    print("La columna id existe")


# --- SECCIÓN 3: Truthy / Falsy (importante en Python) ---

# Son Falsy: None, 0, 0.0, "", [], {}, set()
# Todo lo demás es Truthy.

lista = []
if not lista:
    print("La lista está vacía — no hay datos que procesar")

texto = "  "
if not texto.strip():
    print("El campo de texto está en blanco")


# --- SECCIÓN 4: Validación de registros (patrón ETL) ---

def validar_registro(fila: dict) -> str:
    if fila.get("id") is None:
        return "ERROR: falta id"
    if not isinstance(fila.get("monto"), (int, float)):
        return "ERROR: monto no numérico"
    if fila["monto"] < 0:
        return "ERROR: monto negativo"
    return "OK"

print(validar_registro({"id": 1, "monto": 150.0}))    # OK
print(validar_registro({"id": None, "monto": 50.0}))  # ERROR: falta id
print(validar_registro({"id": 2, "monto": -10}))       # ERROR: monto negativo


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# Clasifica un monto de venta en categorías:
#   >= 10000  -> "premium"
#   >= 5000   -> "alto"
#   >= 1000   -> "medio"
#   < 1000    -> "bajo"
# Imprime: "Venta de 7500.0 clasificada como: alto"

monto = 7500.0
# TODO:


# EJ-2
# Valida si un registro es procesable.
# Un registro es inválido si:
#   - 'fecha' está vacía o es None
#   - 'cantidad' es negativa o cero
#   - 'producto' no está en la lista de productos_validos
# Si es inválido imprime el motivo. Si es válido imprime "Registro válido."

productos_validos = ["arroz", "leche", "aceite", "azucar"]
registro = {"fecha": "2024-03-10", "cantidad": 0, "producto": "arroz"}
# TODO:


# EJ-3
# Dado un dict con el resultado de una conexión a base de datos,
# determina qué acción tomar:
#   - si 'estado' == "ok" y 'filas' > 0    -> "Procesar datos"
#   - si 'estado' == "ok" y 'filas' == 0   -> "Tabla vacía, skip"
#   - si 'estado' == "error"               -> f"Reintentar: {resultado['mensaje']}"
#   - cualquier otro caso                  -> "Estado desconocido"

resultado = {"estado": "ok", "filas": 0, "mensaje": ""}
# TODO:


# EJ-4
# Usando expresión ternaria (una línea), asigna a `etiqueta`:
#   "nulo" si valor es None, de lo contrario el valor convertido a string.
# Prueba con valor = None y luego con valor = 42.

valor = None
# TODO: etiqueta = ...
print(etiqueta)


# EJ-5 (desafío)
# Clasifica una lista de registros en tres listas: validos, nulos, anomalos.
# Un registro es nulo si cualquier valor es None.
# Un registro es anómalo si monto > 100000 (posible error de carga).
# El resto es válido.

registros = [
    {"id": 1, "monto": 500.0},
    {"id": 2, "monto": None},
    {"id": 3, "monto": 250000.0},
    {"id": None, "monto": 100.0},
    {"id": 4, "monto": 3200.0},
]
validos, nulos, anomalos = [], [], []
# TODO: clasifica cada registro en la lista correspondiente
print("Válidos:", validos)
print("Nulos:", nulos)
print("Anómalos:", anomalos)
