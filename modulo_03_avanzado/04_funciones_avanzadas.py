# =============================================================================
# MÓDULO 3 - LECCIÓN 4: Funciones Avanzadas
# =============================================================================
# Generators, context managers, decoradores con parámetros, dataclasses.
#
# Por qué importa en datos:
#   generators     -> procesar archivos enormes sin cargar todo en memoria
#   context managers -> garantizar cierre de conexiones/archivos
#   decoradores    -> reutilizar lógica de retry, timing, validación
#   dataclasses    -> representar esquemas y configuraciones con tipado
# =============================================================================

import time
import os
import csv
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator, Generator


# =============================================================================
# PARTE A — Generators
# =============================================================================
# Un generator es una función que produce valores de a uno usando `yield`.
# No calcula todo de una vez: ideal para archivos grandes o streams.

# --- A1: Generator básico vs lista ---

def cuadrados_lista(n: int) -> list:
    return [i ** 2 for i in range(n)]      # crea toda la lista en memoria

def cuadrados_gen(n: int) -> Generator:
    for i in range(n):
        yield i ** 2                        # produce uno por uno, sin guardar

# Con n=1_000_000: la lista usa ~8MB de RAM; el generator usa ~200 bytes
gen = cuadrados_gen(5)
print(next(gen))   # 0
print(next(gen))   # 1
print(list(gen))   # [4, 9, 16]  (consume el resto)


# --- A2: Generator para leer CSV en lotes (batch reading) ---

def leer_csv_en_lotes(ruta: str, tamanio_lote: int = 1000) -> Iterator[list]:
    """
    Lee un CSV de cualquier tamaño procesando un lote a la vez.
    Nunca carga el archivo completo en memoria.
    """
    with open(ruta, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        lote = []
        for fila in reader:
            lote.append(fila)
            if len(lote) == tamanio_lote:
                yield lote
                lote = []
        if lote:           # último lote (puede ser menor que tamanio_lote)
            yield lote

# Crear CSV de ejemplo
ruta_test = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos", "grande.csv")
os.makedirs(os.path.dirname(ruta_test), exist_ok=True)
with open(ruta_test, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "valor"])
    for i in range(1, 101):
        w.writerow([i, i * 10])

total_filas = 0
for lote in leer_csv_en_lotes(ruta_test, tamanio_lote=25):
    total_filas += len(lote)
    print(f"  Procesando lote de {len(lote)} filas — acumulado: {total_filas}")

print(f"Total procesado: {total_filas} filas")


# --- A3: Generator expression (una línea) ---

numeros = range(1, 11)
pares_cuadrados = sum(x**2 for x in numeros if x % 2 == 0)
print(f"Suma de cuadrados de pares: {pares_cuadrados}")   # 220


# --- A4: Generator con send() — pipeline de transformación ---

def transformador() -> Generator:
    """
    Recibe valores con .send() y los transforma.
    Útil para pipelines de datos tipo coroutine.
    """
    resultado = None
    while True:
        valor = yield resultado
        if valor is None:
            break
        resultado = str(valor).strip().lower().replace(" ", "_")

pipeline = transformador()
next(pipeline)                          # arrancar el generator
print(pipeline.send("  NOMBRE Cliente  "))   # nombre_cliente
print(pipeline.send("REGION NORTE"))          # region_norte


# =============================================================================
# PARTE B — Context Managers
# =============================================================================

# --- B1: contextmanager decorator (la forma más simple) ---

@contextmanager
def temporizador(nombre: str):
    """Mide el tiempo de un bloque with."""
    print(f"[TIMER] Iniciando: {nombre}")
    t0 = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - t0
        print(f"[TIMER] {nombre} completado en {elapsed:.4f}s")

with temporizador("carga de datos"):
    time.sleep(0.05)
    datos = list(range(10_000))


# --- B2: Context manager para conexión simulada ---

@contextmanager
def conexion_db(nombre_db: str):
    """
    Simula abrir/cerrar una conexión a base de datos.
    Garantiza el cierre aunque haya excepción.
    """
    print(f"[DB] Conectando a {nombre_db}...")
    conn = {"db": nombre_db, "abierta": True}   # conexión simulada
    try:
        yield conn
    except Exception as e:
        print(f"[DB] Rollback en {nombre_db}: {e}")
        raise
    finally:
        conn["abierta"] = False
        print(f"[DB] Conexión a {nombre_db} cerrada")

with conexion_db("ventas_dw") as conn:
    print(f"  Usando conexión: {conn}")
    # conn.execute(...) en una BD real


# --- B3: Context manager como clase (para mayor control) ---

class TransaccionCSV:
    """
    Escribe filas a un CSV temporal y, al cerrar con éxito,
    renombra al archivo final. Si hay error, elimina el temporal.
    """
    def __init__(self, ruta_final: str, campos: list):
        self.ruta_final = ruta_final
        self.ruta_temp  = ruta_final + ".tmp"
        self.campos     = campos
        self._file      = None
        self._writer    = None

    def __enter__(self):
        self._file   = open(self.ruta_temp, "w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=self.campos)
        self._writer.writeheader()
        return self._writer

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._file.close()
        if exc_type is None:
            os.replace(self.ruta_temp, self.ruta_final)   # atómico en el mismo disco
            print(f"[CSV] Escrito: {self.ruta_final}")
        else:
            os.remove(self.ruta_temp)
            print(f"[CSV] Error: temporal eliminado")
        return False

ruta_salida = os.path.join(os.path.dirname(ruta_test), "salida_segura.csv")
with TransaccionCSV(ruta_salida, ["id", "valor"]) as writer:
    writer.writerows([{"id": i, "valor": i*5} for i in range(1, 6)])


# =============================================================================
# PARTE C — Decoradores con parámetros
# =============================================================================

# --- C1: Decorador con parámetros ---

def reintentar(max_intentos: int = 3, espera: float = 0.5, excepciones=(Exception,)):
    """
    Reintenta la función hasta max_intentos veces si lanza alguna de las excepciones.
    """
    def decorator(func):
        from functools import wraps
        @wraps(func)
        def wrapper(*args, **kwargs):
            for intento in range(1, max_intentos + 1):
                try:
                    return func(*args, **kwargs)
                except excepciones as e:
                    if intento == max_intentos:
                        raise
                    print(f"  [RETRY {intento}/{max_intentos}] {func.__name__}: {e} — reintentando en {espera}s")
                    time.sleep(espera)
        return wrapper
    return decorator


_llamadas = 0

@reintentar(max_intentos=3, espera=0.1, excepciones=(ConnectionError,))
def conectar_bd():
    global _llamadas
    _llamadas += 1
    if _llamadas < 3:
        raise ConnectionError("timeout")
    print(f"  Conectado en el intento {_llamadas}")

conectar_bd()


# --- C2: Decorador de validación de entrada ---

def validar_no_vacio(*campos):
    """Lanza ValueError si alguno de los argumentos nombrados está vacío o None."""
    def decorator(func):
        from functools import wraps
        import inspect
        sig = inspect.signature(func)
        @wraps(func)
        def wrapper(*args, **kwargs):
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            for campo in campos:
                val = bound.arguments.get(campo)
                if val is None or (isinstance(val, (str, list, dict)) and not val):
                    raise ValueError(f"El parámetro '{campo}' no puede estar vacío")
            return func(*args, **kwargs)
        return wrapper
    return decorator


@validar_no_vacio("tabla", "datos")
def cargar_tabla(tabla: str, datos: list):
    print(f"Cargando {len(datos)} filas en {tabla}")

cargar_tabla("ventas", [{"id": 1}])
try:
    cargar_tabla("", [{"id": 1}])
except ValueError as e:
    print(f"Validación: {e}")


# =============================================================================
# PARTE D — Dataclasses
# =============================================================================

@dataclass
class ConfigPipeline:
    nombre:        str
    fuente:        str
    destino:       str
    lote_tamanio:  int   = 1000
    max_reintentos: int  = 3
    activo:        bool  = True
    etiquetas:     list  = field(default_factory=list)   # mutable default: siempre field()

    def cadena_conexion(self) -> str:
        return f"{self.fuente} -> {self.destino}"


@dataclass(frozen=True)   # inmutable, hashable -> se puede usar como llave de dict
class ClaveParticion:
    anio: int
    mes:  int
    region: str


cfg = ConfigPipeline(nombre="etl_ventas", fuente="s3://raw/ventas", destino="postgresql://dw/ventas")
print(cfg)
print(cfg.cadena_conexion())

clave = ClaveParticion(2024, 3, "norte")
mapa = {clave: 1500.0}
print(mapa[ClaveParticion(2024, 3, "norte")])   # 1500.0


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# Escribe un generator `leer_jsonl(ruta: str)` que lea un archivo .jsonl
# (una línea = un objeto JSON) y yielde un dict por línea.
# Ignora líneas vacías y maneja JSONDecodeError sin detener el generator
# (loggea el error y continúa).
# Pruébalo creando un archivo .jsonl de 5 líneas (una con JSON inválido).

# TODO:


# EJ-2
# Escribe un context manager `directorio_temporal(base_dir: str)`
# que crea un directorio temporal con nombre único (usa os.makedirs),
# lo yielde, y al salir lo elimina con shutil.rmtree() —
# incluso si hubo excepción. Verifica que el directorio se elimina al salir.

import shutil
# TODO:


# EJ-3
# Escribe un decorador `cachear(ttl_seg: int)` que guarde el resultado
# de una función en un dict interno. Si se vuelve a llamar con los mismos
# argumentos dentro de ttl_seg segundos, devuelve el valor cacheado.
# Pasado el ttl, recalcula.
# Pruébalo con una función que tarde 0.5s y verifica el speedup.

# TODO:


# EJ-4
# Define un dataclass `RegistroVenta` con campos:
#   id: int, fecha: str, producto: str, region: str, cantidad: int, precio: float
# Agrega un método `total() -> float` y una propiedad `es_valido: bool`
# que retorne True si cantidad > 0 y precio > 0.
# Crea una lista de 3 instancias e imprime solo las válidas.

# TODO:


# EJ-5 (desafío)
# Implementa un pipeline de generators encadenados:
#   leer_csv(ruta)            -> generator de filas (dicts)
#   filtrar(gen, campo, val)  -> generator que filtra por campo==val
#   transformar(gen, fn)      -> generator que aplica fn a cada fila
#   contar_y_volcar(gen, ruta_salida) -> consume el pipeline, escribe CSV y retorna conteo
#
# Úsalos así:
#   filas   = leer_csv("grande.csv")
#   filtrados = filtrar(filas, "valor", lambda v: int(v) > 300)
#   transformados = transformar(filtrados, lambda f: {**f, "valor_doble": int(f["valor"])*2})
#   n = contar_y_volcar(transformados, "resultado_pipeline.csv")
#   print(f"Filas escritas: {n}")

# TODO:
