# =============================================================================
# MÓDULO 4 - LECCIÓN 1: Anatomía de un Pipeline
# =============================================================================
# Un pipeline es una cadena de pasos donde la salida de uno
# es la entrada del siguiente.
#
# Tipos principales:
#   Batch      -> procesa un volumen fijo de datos de una vez
#   Streaming  -> procesa eventos en tiempo real, uno por uno
#   Micro-batch-> lotes pequeños frecuentes (intermedio)
#
# Componentes de todo pipeline:
#   SOURCE     -> de dónde vienen los datos (API, archivo, BD, cola)
#   TRANSFORM  -> qué le hacemos (limpiar, enriquecer, agregar)
#   SINK       -> a dónde van (BD, S3, dashboard, otro pipeline)
# =============================================================================


# =============================================================================
# PARTE A — Pipeline más simple posible
# =============================================================================

# --- SECCIÓN 1: Tres funciones = pipeline ---

def extraer(fuente: str) -> list:
    """SOURCE: simula leer datos de una fuente."""
    print(f"  [SOURCE] Leyendo desde {fuente}")
    return [
        {"id": 1, "nombre": "  JUAN PEREZ  ", "monto": "150.5",  "region": "norte"},
        {"id": 2, "nombre": "maria garcia",   "monto": "abc",    "region": "SUR"},
        {"id": 3, "nombre": "Pedro Lopez",    "monto": "200.0",  "region": "norte"},
        {"id": 4, "nombre": "ANA QUISPE",     "monto": "-50.0",  "region": "este"},
        {"id": 5, "nombre": "luis mamani",    "monto": "320.75", "region": "sur"},
    ]


def transformar(registros: list) -> list:
    """TRANSFORM: limpia y valida los datos."""
    print(f"  [TRANSFORM] Procesando {len(registros)} registros")
    resultado = []
    for r in registros:
        try:
            monto = float(r["monto"])
            if monto <= 0:
                continue   # descartar inválidos
            resultado.append({
                "id":     r["id"],
                "nombre": r["nombre"].strip().title(),
                "monto":  monto,
                "region": r["region"].strip().lower(),
            })
        except ValueError:
            pass   # saltar si monto no es número
    print(f"  [TRANSFORM] {len(resultado)} válidos de {len(registros)}")
    return resultado


def cargar(registros: list, destino: str) -> int:
    """SINK: simula escribir los datos al destino."""
    print(f"  [SINK] Cargando {len(registros)} registros en {destino}")
    for r in registros:
        print(f"    -> {r}")
    return len(registros)


# Ejecutar el pipeline manualmente paso a paso
print("=== Pipeline manual ===")
datos_crudos   = extraer("ventas_raw.csv")
datos_limpios  = transformar(datos_crudos)
n_cargados     = cargar(datos_limpios, "bd_ventas")
print(f"  Resultado: {n_cargados} filas cargadas\n")


# =============================================================================
# PARTE B — Pipeline como función única
# =============================================================================

# --- SECCIÓN 2: Encapsular el flujo en una función ---

def ejecutar_pipeline(fuente: str, destino: str) -> dict:
    """
    Encapsula todo el flujo en un solo punto de entrada.
    Retorna métricas de la ejecución.
    """
    datos_raw   = extraer(fuente)
    datos_ok    = transformar(datos_raw)
    n_cargados  = cargar(datos_ok, destino)

    return {
        "fuente":          fuente,
        "destino":         destino,
        "registros_in":    len(datos_raw),
        "registros_out":   n_cargados,
        "registros_err":   len(datos_raw) - n_cargados,
    }


print("=== Pipeline encapsulado ===")
metricas = ejecutar_pipeline("ventas_raw.csv", "bd_ventas")
print(f"  Métricas: {metricas}\n")


# =============================================================================
# PARTE C — Pipeline como lista de pasos
# =============================================================================

# --- SECCIÓN 3: Pasos como funciones en una lista ---
# Cada paso recibe datos y devuelve datos transformados.
# La lista define el orden del flujo.

def paso_normalizar_strings(registros: list) -> list:
    for r in registros:
        r["nombre"] = r["nombre"].strip().title()
        r["region"] = r["region"].strip().lower()
    return registros

def paso_convertir_monto(registros: list) -> list:
    resultado = []
    for r in registros:
        try:
            r["monto"] = float(r["monto"])
            resultado.append(r)
        except (ValueError, TypeError):
            pass
    return resultado

def paso_filtrar_negativos(registros: list) -> list:
    return [r for r in registros if r["monto"] > 0]

def paso_agregar_total_con_iva(registros: list) -> list:
    for r in registros:
        r["total_iva"] = round(r["monto"] * 1.16, 2)
    return registros


# El pipeline es simplemente la lista de pasos en orden
pasos = [
    paso_normalizar_strings,
    paso_convertir_monto,
    paso_filtrar_negativos,
    paso_agregar_total_con_iva,
]

def correr_pasos(datos: list, pasos: list) -> list:
    """Aplica cada paso en secuencia sobre los datos."""
    for paso in pasos:
        datos = paso(datos)
        print(f"  [{paso.__name__}] -> {len(datos)} registros")
    return datos

print("=== Pipeline como lista de pasos ===")
datos_iniciales = extraer("ventas_raw.csv")
datos_finales   = correr_pasos(datos_iniciales, pasos)
print(f"\n  Resultado final ({len(datos_finales)} filas):")
for r in datos_finales:
    print(f"    {r}")


# =============================================================================
# PARTE D — Tipos de pipeline según frecuencia
# =============================================================================

# --- SECCIÓN 4: Batch vs Micro-batch ---

import time

def pipeline_batch(registros: list) -> list:
    """Procesa todos los registros de una vez."""
    print(f"[BATCH] Procesando {len(registros)} registros juntos")
    return [{"id": r["id"], "procesado": True} for r in registros]


def pipeline_micro_batch(registros: list, tamanio: int = 2) -> list:
    """Procesa en lotes pequeños — útil para no saturar memoria o la red."""
    todos = []
    for i in range(0, len(registros), tamanio):
        lote = registros[i:i + tamanio]
        print(f"[MICRO-BATCH] Lote {i//tamanio + 1}: {len(lote)} registros")
        time.sleep(0.05)   # simula latencia de procesamiento
        todos.extend([{"id": r["id"], "procesado": True} for r in lote])
    return todos


def pipeline_streaming(registros: list):
    """Procesa de a uno, como si llegaran de una cola en tiempo real."""
    for r in registros:
        print(f"[STREAM] Evento recibido: id={r['id']}")
        yield {"id": r["id"], "procesado": True}
        time.sleep(0.02)   # simula llegada de eventos


datos = [{"id": i} for i in range(1, 7)]

print("\n--- Batch ---")
pipeline_batch(datos)

print("\n--- Micro-batch (tamaño=2) ---")
pipeline_micro_batch(datos, tamanio=2)

print("\n--- Streaming ---")
for evento in pipeline_streaming(datos):
    pass   # en producción aquí harías algo con cada evento


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# Dado este listado de logs de acceso a una API, escribe un pipeline
# de 3 pasos como lista de funciones:
#   1. Filtrar solo los logs con status >= 400 (errores)
#   2. Extraer solo los campos: endpoint, status, usuario
#   3. Agregar una columna "tipo_error": "client" si 400-499, "server" si >= 500
# Luego corre los pasos con correr_pasos() e imprime el resultado.

logs = [
    {"id": 1, "endpoint": "/api/ventas",   "status": 200, "usuario": "u1", "ms": 120},
    {"id": 2, "endpoint": "/api/productos","status": 404, "usuario": "u2", "ms": 45},
    {"id": 3, "endpoint": "/api/ventas",   "status": 500, "usuario": "u1", "ms": 980},
    {"id": 4, "endpoint": "/api/usuarios", "status": 403, "usuario": "u3", "ms": 30},
    {"id": 5, "endpoint": "/api/ventas",   "status": 200, "usuario": "u2", "ms": 150},
    {"id": 6, "endpoint": "/api/reportes", "status": 503, "usuario": "u1", "ms": 5000},
]
# TODO:


# EJ-2
# Implementa `pipeline_con_log(datos, pasos)` igual que correr_pasos()
# pero que imprima para cada paso:
#   [PASO 1/3] paso_normalizar_strings | in=5 | out=5 | 0.002s
# Usa time.perf_counter() para medir la duración de cada paso.

# TODO:


# EJ-3
# Escribe un pipeline micro-batch que:
#   1. Reciba una lista de 20 registros (genera con range)
#   2. Los procese en lotes de 5
#   3. En cada lote: filtre los que tengan id par y los multiplique por 10
#   4. Acumule resultados y retorne lista final
# Imprime el lote procesado en cada iteración.

# TODO:


# EJ-4
# Convierte el pipeline de la Parte C en un generator (streaming).
# Cada paso debe procesar y yieldar de a un elemento.
# Encadena los generators para que el flujo sea lazy:
#   stream = agregar_iva(filtrar(convertir(normalizar(iter(datos)))))
# Itera el stream final e imprime cada elemento.

# TODO:


# EJ-5 (desafío)
# Implementa `pipeline_bifurcado(datos, rama_a, rama_b, condicion)`:
# Divide los datos en dos según `condicion(registro) -> bool`.
# Los que cumplen van por rama_a (lista de pasos), los que no por rama_b.
# Retorna (resultado_a, resultado_b).
#
# Pruébalo con:
#   - condicion: region == "norte"
#   - rama_a: agregar columna "prioridad" = "alta"
#   - rama_b: agregar columna "prioridad" = "normal"

# TODO:
