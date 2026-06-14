# =============================================================================
# MÓDULO 3 - LECCIÓN 4: Python Avanzado para Datos
# =============================================================================
# Herramientas del lenguaje que hacen el código más limpio, eficiente
# y pythónico en contextos de ingeniería de datos:
#
#   - Generadores        -> procesar datos grandes sin cargar en memoria
#   - Context managers   -> gestión de recursos (archivos, conexiones)
#   - Dataclasses        -> estructuras de datos tipadas sin boilerplate
#   - typing             -> type hints avanzados
#   - itertools          -> combinaciones, agrupaciones, cadenas
#   - collections        -> Counter, defaultdict, namedtuple
# =============================================================================

import itertools
from collections import Counter, defaultdict, namedtuple
from dataclasses import dataclass, field
from typing import Generator, Iterator, Optional
from contextlib import contextmanager
import time


# =============================================================================
# PARTE A — Generadores
# =============================================================================
# Un generador produce valores de uno en uno con `yield`.
# No carga todo en memoria: ideal para archivos grandes o streams.

# --- A1: Función generadora básica ---

def contar_hasta(n: int) -> Generator[int, None, None]:
    i = 0
    while i < n:
        yield i
        i += 1

for num in contar_hasta(5):
    print(num, end=" ")
print()

# Equivalente con list pero sin cargar todo en memoria:
lista = list(contar_hasta(1_000_000))   # usa ~8MB de RAM
gen   = contar_hasta(1_000_000)         # usa ~200 bytes


# --- A2: Leer CSV por lotes sin cargar todo el archivo ---

def leer_csv_en_lotes(ruta: str, tamanio_lote: int = 100) -> Generator[list, None, None]:
    """Yield lotes de `tamanio_lote` filas para no saturar la RAM."""
    import csv
    with open(ruta, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        lote = []
        for fila in reader:
            lote.append(fila)
            if len(lote) >= tamanio_lote:
                yield lote
                lote = []
        if lote:          # último lote (puede ser < tamanio_lote)
            yield lote

# Uso:
# for lote in leer_csv_en_lotes("datos/ventas_grandes.csv", tamanio_lote=500):
#     procesar(lote)


# --- A3: Generador de pipeline (composición) ---

def filtrar(registros: Iterator, campo: str, valor) -> Generator:
    for r in registros:
        if r.get(campo) == valor:
            yield r

def agregar_total(registros: Iterator) -> Generator:
    for r in registros:
        r["total"] = float(r.get("cantidad", 0)) * float(r.get("precio", 0))
        yield r

ventas_raw = [
    {"id": "1", "region": "norte", "cantidad": "100", "precio": "12.50"},
    {"id": "2", "region": "sur",   "cantidad": "200", "precio": "8.00"},
    {"id": "3", "region": "norte", "cantidad": "80",  "precio": "25.00"},
]

# Componer generadores sin listas intermedias
pipeline = agregar_total(filtrar(iter(ventas_raw), "region", "norte"))
for registro in pipeline:
    print(f"  id={registro['id']}, total={registro['total']}")


# =============================================================================
# PARTE B — Context Managers
# =============================================================================

# --- B1: contextmanager decorator (más simple que __enter__/__exit__) ---

@contextmanager
def cronometrar(nombre: str):
    """Mide el tiempo de un bloque de código."""
    t0 = time.perf_counter()
    print(f"[⏱] {nombre} — iniciando")
    try:
        yield
    finally:
        elapsed = time.perf_counter() - t0
        print(f"[⏱] {nombre} — {elapsed:.3f}s")

with cronometrar("carga de datos"):
    time.sleep(0.05)
    datos = list(range(10_000))


# --- B2: Context manager para conexión simulada ---

@contextmanager
def conexion_bd(host: str, db: str):
    """Simula abrir/cerrar conexión a BD."""
    print(f"[DB] Conectando a {host}/{db}")
    conexion = {"host": host, "db": db, "activa": True}
    try:
        yield conexion
    except Exception as e:
        print(f"[DB] Error — haciendo rollback: {e}")
        raise
    finally:
        conexion["activa"] = False
        print(f"[DB] Conexión cerrada")

with conexion_bd("localhost", "ventas") as conn:
    print(f"  Ejecutando query en {conn['db']}")


# =============================================================================
# PARTE C — Dataclasses
# =============================================================================
# Alternativa limpia a dicts para datos estructurados.
# Ventajas: type hints, repr automático, comparación, validación.

@dataclass
class Venta:
    id:       int
    fecha:    str
    producto: str
    region:   str
    cantidad: int
    precio:   float
    total:    float = field(init=False)

    def __post_init__(self):
        self.total = round(self.cantidad * self.precio, 2)
        # Validación en la creación
        if self.cantidad <= 0:
            raise ValueError(f"Venta {self.id}: cantidad debe ser positiva")
        if self.precio <= 0:
            raise ValueError(f"Venta {self.id}: precio debe ser positivo")


@dataclass
class ResultadoEtapa:
    etapa:            str
    filas_entrada:    int
    filas_salida:     int
    filas_rechazadas: int = 0
    duracion_seg:     float = 0.0
    estado:           str = "ok"

    @property
    def tasa_rechazo(self) -> float:
        if self.filas_entrada == 0:
            return 0.0
        return round(self.filas_rechazadas / self.filas_entrada * 100, 1)


v1 = Venta(1, "2024-01-10", "arroz", "norte", 100, 12.50)
print(v1)
print(f"Total: {v1.total}")

res = ResultadoEtapa("transform", filas_entrada=1000, filas_salida=985, filas_rechazadas=15, duracion_seg=1.2)
print(res)
print(f"Tasa rechazo: {res.tasa_rechazo}%")

try:
    v_invalida = Venta(99, "2024-01-01", "sal", "sur", -5, 3.0)
except ValueError as e:
    print(f"Error esperado: {e}")


# =============================================================================
# PARTE D — collections
# =============================================================================

# --- D1: Counter ---
productos_vendidos = ["arroz", "leche", "arroz", "aceite", "arroz", "leche", "azucar"]
conteo = Counter(productos_vendidos)
print(f"\nConteo: {conteo}")
print(f"Top 2: {conteo.most_common(2)}")

# --- D2: defaultdict — evita KeyError al acumular ---
ventas_por_region: dict[str, list] = defaultdict(list)
ventas_data = [("norte", 1200), ("sur", 800), ("norte", 1500), ("sur", 600)]
for region, monto in ventas_data:
    ventas_por_region[region].append(monto)

print(f"\nVentas por región: {dict(ventas_por_region)}")
totales = {r: sum(v) for r, v in ventas_por_region.items()}
print(f"Totales: {totales}")

# --- D3: namedtuple — tuplas con nombres de campo ---
Registro = namedtuple("Registro", ["id", "producto", "monto"])
r = Registro(id=1, producto="arroz", monto=150.0)
print(f"\nRegistro: {r}")
print(f"Producto: {r.producto}")


# =============================================================================
# PARTE E — itertools
# =============================================================================

# chain — concatenar iterables
norte = [("a", 100), ("b", 200)]
sur   = [("c", 300), ("d", 400)]
todos = list(itertools.chain(norte, sur))
print(f"\nChain: {todos}")

# groupby — agrupar (requiere que estén ordenados por clave)
registros = [
    {"region": "este",  "monto": 100},
    {"region": "norte", "monto": 200},
    {"region": "norte", "monto": 300},
    {"region": "sur",   "monto": 150},
    {"region": "sur",   "monto": 250},
]
registros.sort(key=lambda x: x["region"])
for region, grupo in itertools.groupby(registros, key=lambda x: x["region"]):
    montos = [r["monto"] for r in grupo]
    print(f"  {region}: suma={sum(montos)}")

# islice — tomar solo N elementos de un generador
primeros_3 = list(itertools.islice(contar_hasta(1_000_000), 3))
print(f"\nPrimeros 3: {primeros_3}")

# product — producto cartesiano (útil para generar particiones)
anios  = [2023, 2024]
meses  = [1, 2, 3]
particiones = list(itertools.product(anios, meses))
print(f"Particiones: {particiones}")


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# Escribe un generador `generar_particiones(fecha_inicio: str, fecha_fin: str)`
# que yield strings de partición en formato "YYYY/MM" para cada mes entre
# las dos fechas (inclusive).
# Ejemplo: generar_particiones("2024-01", "2024-04") yields:
#   "2024/01", "2024/02", "2024/03", "2024/04"
# PISTA: usa itertools.product o un while loop con datetime.

# TODO:


# EJ-2
# Crea un dataclass `ConfigPipeline` con campos:
#   nombre: str, fuente: str, destino: str,
#   max_filas_lote: int = 1000, reintentos: int = 3, activo: bool = True
# Agrega un método `validar()` que lance ValueError si nombre está vacío
# o max_filas_lote < 1. Prueba con configuraciones válidas e inválidas.

# TODO:


# EJ-3
# Usa Counter para analizar la siguiente lista de eventos de pipeline
# y determinar: total por tipo, el tipo más frecuente, cuántos son errores.

eventos = [
    "INFO", "INFO", "DEBUG", "WARNING", "ERROR", "INFO",
    "DEBUG", "ERROR", "INFO", "WARNING", "CRITICAL", "INFO",
    "ERROR", "DEBUG", "INFO",
]
# TODO:


# EJ-4
# Escribe un context manager `transaccion_bd(conexion)` usando @contextmanager
# que simule una transacción:
#   - Al entrar: imprime "BEGIN TRANSACTION"
#   - Al salir sin error: imprime "COMMIT"
#   - Al salir con error: imprime "ROLLBACK" y re-lanza la excepción
# Pruébalo con un bloque que falla y otro que tiene éxito.

# TODO:


# EJ-5 (desafío)
# Implementa un pipeline de procesamiento lazy (sin listas intermedias)
# usando generadores encadenados para procesar este archivo grande simulado:
#
#   1. leer_registros(n)     -> genera n registros simulados como dicts
#   2. limpiar(registros)    -> strip de strings, descarta los con id None
#   3. enriquecer(registros) -> agrega campo "total" = cantidad * precio
#   4. filtrar_validos(registros) -> solo total > 0
#   5. en_lotes(registros, tamanio) -> agrupa en listas de `tamanio`
#
# Encadénalos y procesa 10_000 registros en lotes de 200.
# Imprime el número de lotes procesados y la suma total de todos los totales.

# TODO:
