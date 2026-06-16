# =============================================================================
# MÓDULO 4 - LECCIÓN 4: Pipeline Resiliente
# =============================================================================
# Un pipeline de producción debe sobrevivir fallos parciales.
# Conceptos clave:
#
#   Idempotencia   -> ejecutar N veces = mismo resultado (sin duplicados)
#   Checkpointing  -> guardar estado intermedio para reanudar si falla
#   Dead Letter    -> separar filas fallidas para revisión posterior
#   Retry          -> reintentar operaciones con backoff exponencial
#   Circuit Breaker-> dejar de reintentar si el sistema remoto está caído
# =============================================================================

import json
import os
import time
import hashlib
from dataclasses import dataclass, field
from typing import Callable, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(BASE_DIR, "datos", "estado")
os.makedirs(STATE_DIR, exist_ok=True)


# =============================================================================
# PARTE A — Idempotencia
# =============================================================================

# --- SECCIÓN 1: ¿Qué es idempotencia? ---
# Una operación es idempotente si ejecutarla múltiples veces tiene el
# mismo efecto que ejecutarla una sola vez.
#
# En datos: si el pipeline falla a la mitad y lo volvemos a correr,
# no debemos tener filas duplicadas en el destino.

# Estrategia 1: INSERT OR REPLACE (SQLite)
import sqlite3

DB = os.path.join(STATE_DIR, "demo.db")

def setup_db():
    with sqlite3.connect(DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ventas_procesadas (
                id      INTEGER PRIMARY KEY,    -- PK previene duplicados
                fecha   TEXT,
                total   REAL,
                cargado TEXT
            )
        """)

def insertar_idempotente(registros: list):
    """INSERT OR REPLACE garantiza que re-correr no duplica filas."""
    with sqlite3.connect(DB) as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO ventas_procesadas (id, fecha, total, cargado) VALUES (?,?,?,?)",
            [(r["id"], r["fecha"], r["total"], r["cargado"]) for r in registros]
        )
    print(f"  [DB] {len(registros)} filas upserted (sin duplicados)")

setup_db()
datos = [
    {"id": 1, "fecha": "2024-01-10", "total": 1250.0, "cargado": "2024-06-14"},
    {"id": 2, "fecha": "2024-01-11", "total": 800.0,  "cargado": "2024-06-14"},
]
insertar_idempotente(datos)
insertar_idempotente(datos)   # segunda ejecución — no genera duplicados

with sqlite3.connect(DB) as conn:
    count = conn.execute("SELECT COUNT(*) FROM ventas_procesadas").fetchone()[0]
print(f"  Filas en BD: {count} (debería ser 2, no 4)")


# Estrategia 2: hash de contenido como id único
def generar_hash_registro(registro: dict, campos: list) -> str:
    """Genera un hash MD5 basado en los campos clave del registro."""
    contenido = "|".join(str(registro.get(c, "")) for c in sorted(campos))
    return hashlib.md5(contenido.encode()).hexdigest()[:12]

reg = {"fecha": "2024-01-10", "producto": "arroz", "region": "norte", "total": 1250.0}
hash_id = generar_hash_registro(reg, campos=["fecha", "producto", "region"])
print(f"\n  Hash del registro: {hash_id}")
# Mismo registro -> mismo hash -> no se duplica


# =============================================================================
# PARTE B — Checkpointing
# =============================================================================

# --- SECCIÓN 2: Guardar y restaurar estado intermedio ---

class Checkpoint:
    """
    Persiste el estado de un pipeline en disco.
    Permite reanudar desde el último paso exitoso si falla.
    """

    def __init__(self, nombre: str, directorio: str = STATE_DIR):
        self.nombre     = nombre
        self.ruta       = os.path.join(directorio, f"{nombre}_checkpoint.json")
        self._estado    = self._cargar()

    def _cargar(self) -> dict:
        if os.path.exists(self.ruta):
            with open(self.ruta, encoding="utf-8") as f:
                estado = json.load(f)
            print(f"  [CHECKPOINT] Restaurado desde {self.ruta}")
            return estado
        return {"paso_actual": 0, "datos": None, "completado": False}

    def guardar(self, paso: int, datos: list):
        self._estado = {"paso_actual": paso, "datos": datos, "completado": False}
        with open(self.ruta, "w", encoding="utf-8") as f:
            json.dump(self._estado, f)
        print(f"  [CHECKPOINT] Guardado en paso {paso}")

    def completar(self):
        self._estado["completado"] = True
        with open(self.ruta, "w", encoding="utf-8") as f:
            json.dump(self._estado, f)
        print(f"  [CHECKPOINT] Pipeline completado — limpiando checkpoint")

    def limpiar(self):
        if os.path.exists(self.ruta):
            os.remove(self.ruta)

    @property
    def paso_actual(self) -> int:
        return self._estado["paso_actual"]

    @property
    def datos_guardados(self) -> Optional[list]:
        return self._estado.get("datos")

    @property
    def completado(self) -> bool:
        return self._estado["completado"]


def pipeline_con_checkpoint(datos: list, pasos: list, nombre: str) -> list:
    """
    Ejecuta pasos con checkpointing.
    Si falla y se vuelve a llamar, reanuda desde el último paso exitoso.
    """
    cp = Checkpoint(nombre)

    if cp.completado:
        print("  [CHECKPOINT] Ya completado anteriormente")
        cp.limpiar()
        return cp.datos_guardados or []

    # Restaurar desde donde quedó
    inicio = cp.paso_actual
    datos_actuales = cp.datos_guardados if inicio > 0 else datos

    for i, (nombre_paso, fn) in enumerate(pasos):
        if i < inicio:
            print(f"  [SKIP] Paso {i}: {nombre_paso} (ya ejecutado)")
            continue
        print(f"  [PASO {i}] {nombre_paso}")
        datos_actuales = fn(datos_actuales)
        cp.guardar(i + 1, datos_actuales)

    cp.completar()
    cp.limpiar()
    return datos_actuales


pasos_demo = [
    ("normalizar",    lambda d: [{**r, "nombre": r["nombre"].strip().lower()} for r in d]),
    ("calcular_total",lambda d: [{**r, "total": r["cantidad"] * r["precio"]} for r in d]),
    ("filtrar",       lambda d: [r for r in d if r["total"] > 100]),
]

datos_prueba = [
    {"nombre": " ARROZ ", "cantidad": 100, "precio": 12.5},
    {"nombre": "LECHE",   "cantidad": 5,   "precio": 8.0},
    {"nombre": " ACEITE", "cantidad": 50,  "precio": 25.0},
]

print("\n--- Primera ejecución ---")
res = pipeline_con_checkpoint(datos_prueba, pasos_demo, "demo_cp")
print(f"  Resultado: {res}")

print("\n--- Segunda ejecución (mismo pipeline) ---")
res2 = pipeline_con_checkpoint(datos_prueba, pasos_demo, "demo_cp")


# =============================================================================
# PARTE C — Dead Letter Queue
# =============================================================================

# --- SECCIÓN 3: Separar filas fallidas ---

@dataclass
class ResultadoProcesamiento:
    exitosos:  list = field(default_factory=list)
    fallidos:  list = field(default_factory=list)   # dead letter

    @property
    def tasa_exito(self) -> float:
        total = len(self.exitosos) + len(self.fallidos)
        return len(self.exitosos) / total * 100 if total else 0.0


def procesar_con_dlq(registros: list, fn: Callable) -> ResultadoProcesamiento:
    """
    Aplica fn a cada registro individualmente.
    Los que fallan van al dead letter queue en lugar de abortar todo.
    """
    resultado = ResultadoProcesamiento()
    for r in registros:
        try:
            procesado = fn(r)
            resultado.exitosos.append(procesado)
        except Exception as e:
            resultado.fallidos.append({"registro_original": r, "error": str(e)})
    return resultado


def transformar_registro(r: dict) -> dict:
    cantidad = int(r["cantidad"])     # falla si no es numérico
    precio   = float(r["precio"])     # falla si no es numérico
    if cantidad <= 0:
        raise ValueError("cantidad debe ser positiva")
    return {**r, "cantidad": cantidad, "precio": precio,
            "total": round(cantidad * precio, 2)}


registros_mixtos = [
    {"id": 1, "cantidad": "100", "precio": "12.5"},
    {"id": 2, "cantidad": "abc", "precio": "8.0"},    # error
    {"id": 3, "cantidad": "-50", "precio": "25.0"},   # error
    {"id": 4, "cantidad": "80",  "precio": "9.75"},
    {"id": 5, "cantidad": "200", "precio": "N/A"},    # error
]

resultado = procesar_con_dlq(registros_mixtos, transformar_registro)
print(f"\n  Exitosos: {len(resultado.exitosos)} | Fallidos: {len(resultado.fallidos)}")
print(f"  Tasa de éxito: {resultado.tasa_exito:.1f}%")
print(f"  Dead Letter Queue: {resultado.fallidos}")

# Guardar DLQ en archivo para revisión posterior
dlq_path = os.path.join(STATE_DIR, "dead_letter.json")
with open(dlq_path, "w") as f:
    json.dump(resultado.fallidos, f, indent=2)
print(f"  DLQ guardado en: {dlq_path}")


# =============================================================================
# PARTE D — Retry con backoff exponencial
# =============================================================================

# --- SECCIÓN 4: Reintentar con espera creciente ---

def retry(max_intentos: int = 3, backoff_base: float = 0.5,
          excepciones: tuple = (Exception,)) -> Callable:
    """
    Decorador: reintenta la función con espera exponencial entre intentos.
    backoff_base * 2^intento segundos de espera.
    """
    def decorator(fn: Callable) -> Callable:
        from functools import wraps
        @wraps(fn)
        def wrapper(*args, **kwargs):
            ultimo_error = None
            for intento in range(1, max_intentos + 1):
                try:
                    return fn(*args, **kwargs)
                except excepciones as e:
                    ultimo_error = e
                    if intento == max_intentos:
                        break
                    espera = backoff_base * (2 ** (intento - 1))
                    print(f"  [RETRY {intento}/{max_intentos}] {fn.__name__}: {e} — espera {espera:.1f}s")
                    time.sleep(espera)
            raise ultimo_error
        return wrapper
    return decorator


# Simular una función que falla las primeras N veces
_contador_conexion = 0

@retry(max_intentos=4, backoff_base=0.1, excepciones=(ConnectionError,))
def conectar_bd(host: str):
    global _contador_conexion
    _contador_conexion += 1
    if _contador_conexion < 3:
        raise ConnectionError(f"Timeout conectando a {host}")
    print(f"  [OK] Conectado a {host} en intento {_contador_conexion}")
    return {"host": host, "estado": "conectado"}

print("\n--- Retry ---")
conn = conectar_bd("db.empresa.com")


# =============================================================================
# PARTE E — Circuit Breaker
# =============================================================================

# --- SECCIÓN 5: Abrir el circuito cuando hay demasiados fallos ---

class CircuitBreaker:
    """
    Deja de llamar a una función si falla demasiadas veces seguidas.
    Estados: CLOSED (normal) -> OPEN (fallando) -> HALF_OPEN (probando)
    """
    CLOSED    = "CLOSED"
    OPEN      = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(self, umbral_fallos: int = 3, tiempo_reset: float = 5.0):
        self.umbral        = umbral_fallos
        self.tiempo_reset  = tiempo_reset
        self.fallos        = 0
        self.estado        = self.CLOSED
        self._ultimo_fallo: Optional[float] = None

    def llamar(self, fn: Callable, *args, **kwargs):
        if self.estado == self.OPEN:
            if time.time() - self._ultimo_fallo > self.tiempo_reset:
                self.estado = self.HALF_OPEN
                print(f"  [CB] Estado -> HALF_OPEN, probando...")
            else:
                raise RuntimeError("Circuit Breaker ABIERTO — servicio no disponible")

        try:
            resultado = fn(*args, **kwargs)
            if self.estado == self.HALF_OPEN:
                self.estado = self.CLOSED
                self.fallos = 0
                print(f"  [CB] Recuperado -> CLOSED")
            return resultado
        except Exception as e:
            self.fallos += 1
            self._ultimo_fallo = time.time()
            if self.fallos >= self.umbral:
                self.estado = self.OPEN
                print(f"  [CB] {self.fallos} fallos -> OPEN. Deteniendo llamadas.")
            raise

    @property
    def disponible(self) -> bool:
        return self.estado != self.OPEN


def api_inestable(n: int) -> dict:
    """Simula API que falla en llamadas impares."""
    if n % 2 != 0:
        raise ConnectionError(f"API caída en llamada {n}")
    return {"dato": n * 10}


cb = CircuitBreaker(umbral_fallos=2, tiempo_reset=1.0)
print("\n--- Circuit Breaker ---")
for i in range(1, 7):
    try:
        res = cb.llamar(api_inestable, i)
        print(f"  Llamada {i}: OK -> {res}")
    except RuntimeError as e:
        print(f"  Llamada {i}: {e}")
    except ConnectionError as e:
        print(f"  Llamada {i}: {e}")


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# Implementa una función `cargar_idempotente(registros, tabla, conn)`
# que use el hash MD5 de los campos (fecha + producto + region) como id
# para evitar duplicados al insertar en SQLite.
# Prueba insertando el mismo lote dos veces y verifica el conteo final.

# TODO:


# EJ-2
# Agrega checkpointing al Pipeline de la lección anterior (clase Pipeline).
# El método run() debe:
#   1. Guardar el estado después de cada paso exitoso
#   2. Si run() se llama de nuevo sobre un pipeline con checkpoint, reanudar
#      desde el paso donde quedó
#   3. Limpiar el checkpoint al completar

# TODO:


# EJ-3
# Crea un pipeline completo con Dead Letter Queue:
#   - Lee una lista de 10 registros (mezcla de válidos e inválidos)
#   - Transforma cada uno con procesar_con_dlq()
#   - Los exitosos se cargan en SQLite
#   - Los fallidos se guardan en dead_letter.json con timestamp
#   - Imprime un resumen: exitosos / fallidos / tasa de éxito

registros_completos = [
    {"id": i, "cantidad": str(i*10 if i % 3 != 0 else "ERROR"), "precio": str(round(i*1.5, 2))}
    for i in range(1, 11)
]
# TODO:


# EJ-4
# Modifica el decorador @retry para que acepte un parámetro
# `on_retry: Callable` que se llame en cada reintento con
# (intento, max_intentos, excepcion, espera_seg).
# Úsalo para loggear los reintentos con el módulo logging.

# TODO:


# EJ-5 (desafío)
# Implementa un pipeline resiliente completo que combine los 4 conceptos:
#   1. Idempotencia: usa hash para detectar y saltar registros ya procesados
#   2. Checkpoint: guarda estado después de cada paso
#   3. DLQ: registros que fallan van al dead letter queue
#   4. Retry: las operaciones de I/O se reintentan hasta 3 veces
# Simula un fallo en el paso 2 (lanza excepción en la primera ejecución),
# vuelve a correr el pipeline y verifica que retoma desde el paso 2.

# TODO:
