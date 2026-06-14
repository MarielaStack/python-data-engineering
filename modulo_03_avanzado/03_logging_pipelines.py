# =============================================================================
# MÓDULO 3 - LECCIÓN 3: Logging de Pipelines
# =============================================================================
# El módulo `logging` de stdlib es la herramienta estándar para registrar
# eventos en aplicaciones Python. Es MUCHO mejor que usar print() en producción.
#
# Por qué no usar print():
#   - No tiene niveles de severidad
#   - No incluye timestamp ni nombre del módulo
#   - No puedes desactivar mensajes de debug sin editar el código
#   - No escribe a archivo sin redirección manual
#
# Niveles (de menor a mayor severidad):
#   DEBUG    -> detalles internos (solo en desarrollo)
#   INFO     -> eventos normales del flujo
#   WARNING  -> algo inesperado pero no fatal
#   ERROR    -> algo falló pero el programa sigue
#   CRITICAL -> fallo grave, el pipeline debe detenerse
# =============================================================================

import logging
import logging.handlers
import json
import os
import time
from datetime import datetime
from functools import wraps

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)


# =============================================================================
# PARTE A — Logger básico
# =============================================================================

# --- A1: Configuración mínima ---

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("pipeline.basico")

logger.debug("Iniciando configuración del pipeline")
logger.info("Pipeline iniciado correctamente")
logger.warning("El archivo de configuración no tiene campo 'timeout', usando default=30s")
logger.error("Falló la conexión a la base de datos destino")
logger.critical("Disco lleno: no se puede continuar")


# =============================================================================
# PARTE B — Logger con archivo + consola (producción)
# =============================================================================

def crear_logger(nombre: str, nivel_consola=logging.INFO, nivel_archivo=logging.DEBUG) -> logging.Logger:
    """
    Crea un logger con dos handlers:
      - consola: solo INFO y superior
      - archivo rotativo: DEBUG y superior (máx 5MB, 3 archivos de respaldo)
    """
    log = logging.getLogger(nombre)
    log.setLevel(logging.DEBUG)   # el logger acepta todo; los handlers filtran

    if log.handlers:
        return log   # evitar agregar handlers duplicados

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler consola
    ch = logging.StreamHandler()
    ch.setLevel(nivel_consola)
    ch.setFormatter(fmt)
    log.addHandler(ch)

    # Handler archivo rotativo
    ruta_log = os.path.join(LOG_DIR, f"{nombre.replace('.', '_')}.log")
    fh = logging.handlers.RotatingFileHandler(
        ruta_log, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(nivel_archivo)
    fh.setFormatter(fmt)
    log.addHandler(fh)

    return log


pipeline_log = crear_logger("pipeline.ventas")
pipeline_log.info("Logger de producción configurado")
pipeline_log.debug("Esto solo aparece en el archivo, no en consola")


# =============================================================================
# PARTE C — Logging estructurado (JSON) para sistemas centralizados
# =============================================================================
# En producción los logs se envían a sistemas como Elasticsearch, Datadog,
# CloudWatch. Estos esperan JSON con campos fijos.

class JSONFormatter(logging.Formatter):
    """Formatea cada log como una línea JSON."""

    CAMPOS_EXTRA = ("pipeline", "etapa", "tabla", "filas", "duracion_seg")

    def format(self, record: logging.LogRecord) -> str:
        log_dict = {
            "timestamp":  self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level":      record.levelname,
            "logger":     record.name,
            "mensaje":    record.getMessage(),
        }
        for campo in self.CAMPOS_EXTRA:
            if hasattr(record, campo):
                log_dict[campo] = getattr(record, campo)
        if record.exc_info:
            log_dict["excepcion"] = self.formatException(record.exc_info)
        return json.dumps(log_dict, ensure_ascii=False)


def crear_logger_json(nombre: str) -> logging.Logger:
    log = logging.getLogger(f"json.{nombre}")
    log.setLevel(logging.DEBUG)
    if log.handlers:
        return log

    ruta = os.path.join(LOG_DIR, f"{nombre}_structured.jsonl")
    fh = logging.FileHandler(ruta, encoding="utf-8")
    fh.setFormatter(JSONFormatter())
    log.addHandler(fh)

    # también a consola legible
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s", "%H:%M:%S"))
    log.addHandler(ch)

    return log


jlog = crear_logger_json("etl")

# Agregar campos extra al log con el parámetro `extra`
jlog.info("Extracción completada", extra={"pipeline": "ventas", "etapa": "extract", "filas": 1500})
jlog.warning("Precio discrepante detectado", extra={"pipeline": "ventas", "etapa": "transform", "filas": 3})
jlog.error("Fallo al escribir en destino", extra={"pipeline": "ventas", "etapa": "load", "tabla": "ventas_dw"})


# =============================================================================
# PARTE D — Decorador para medir y loggear ejecución
# =============================================================================

def loggear_etapa(logger: logging.Logger):
    """
    Decorador que registra inicio, fin y duración de una función.
    Si lanza excepción, la loggea como ERROR y la re-lanza.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nombre = func.__name__
            logger.info(f"[INICIO] {nombre}")
            t0 = time.perf_counter()
            try:
                resultado = func(*args, **kwargs)
                duracion = time.perf_counter() - t0
                logger.info(f"[FIN]   {nombre} | {duracion:.3f}s")
                return resultado
            except Exception as e:
                duracion = time.perf_counter() - t0
                logger.error(f"[ERROR] {nombre} | {duracion:.3f}s | {e}", exc_info=True)
                raise
        return wrapper
    return decorator


etl_log = crear_logger("pipeline.etl")

@loggear_etapa(etl_log)
def extraer_datos(fuente: str) -> list:
    etl_log.debug(f"Leyendo desde: {fuente}")
    time.sleep(0.05)   # simula I/O
    return [{"id": i, "valor": i * 10} for i in range(1, 6)]

@loggear_etapa(etl_log)
def transformar_datos(datos: list) -> list:
    return [{"id": d["id"], "valor_doble": d["valor"] * 2} for d in datos]

@loggear_etapa(etl_log)
def cargar_datos(datos: list, destino: str):
    etl_log.info(f"Cargando {len(datos)} filas en {destino}")
    time.sleep(0.02)

datos_raw   = extraer_datos("ventas.csv")
datos_trans = transformar_datos(datos_raw)
cargar_datos(datos_trans, "db.ventas")


# =============================================================================
# PARTE E — Context manager para sesión de pipeline
# =============================================================================

class SesionPipeline:
    """
    Context manager que loggea inicio/fin de una sesión ETL
    y captura métricas básicas.
    """
    def __init__(self, nombre: str, logger: logging.Logger):
        self.nombre  = nombre
        self.logger  = logger
        self.inicio  = None
        self.metricas: dict = {}

    def __enter__(self):
        self.inicio = time.perf_counter()
        self.logger.info(f"{'='*20} PIPELINE [{self.nombre}] INICIADO {'='*20}")
        return self

    def registrar(self, **kwargs):
        self.metricas.update(kwargs)

    def __exit__(self, exc_type, exc_val, exc_tb):
        duracion = time.perf_counter() - self.inicio
        if exc_type:
            self.logger.error(
                f"PIPELINE [{self.nombre}] FALLIDO | {duracion:.2f}s | {exc_val}",
                exc_info=True,
            )
        else:
            self.logger.info(
                f"PIPELINE [{self.nombre}] COMPLETADO | {duracion:.2f}s | {self.metricas}"
            )
        return False   # no suprimir excepciones


with SesionPipeline("ventas_diarias", etl_log) as sesion:
    datos = extraer_datos("fuente.csv")
    sesion.registrar(filas_extraidas=len(datos))
    resultado = transformar_datos(datos)
    sesion.registrar(filas_transformadas=len(resultado))
    cargar_datos(resultado, "destino.db")
    sesion.registrar(estado="ok")


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# Crea un logger llamado "pipeline.inventario" con:
#   - Handler de consola nivel WARNING
#   - Handler de archivo nivel DEBUG en logs/inventario.log
# Loggea al menos un mensaje de cada nivel y verifica que en consola
# solo aparecen WARNING, ERROR y CRITICAL, pero en el archivo aparecen todos.

# TODO:


# EJ-2
# Escribe un decorador `reintentar(max_intentos=3, logger=None)` que:
#   - Reintente la función hasta max_intentos veces si lanza excepción
#   - Loggee cada reintento como WARNING
#   - Loggee el éxito final como INFO
#   - Si se agotan los intentos, loggee como ERROR y re-lance la excepción
#
# Pruébalo con una función que falla las 2 primeras llamadas.

intentos_globales = 0  # variable auxiliar para la simulación
# TODO: def reintentar(max_intentos=3, logger=None): ...


# EJ-3
# Extiende JSONFormatter para incluir también:
#   - "host": nombre del equipo (usa socket.gethostname())
#   - "pid": ID del proceso (usa os.getpid())
# Crea un logger con este formatter y loggea 3 eventos.

import socket
# TODO:


# EJ-4
# Usa SesionPipeline para envolver este pipeline de 3 etapas.
# Registra: filas_entrada, filas_salida, archivos_escritos.
# Simula un error en la etapa de carga (raise ValueError("disco lleno"))
# y verifica que el context manager loggea el error correctamente.

# TODO:


# EJ-5 (desafío)
# Implementa `LectorLogsPipeline(ruta_jsonl: str)` que lea el archivo
# .jsonl generado por JSONFormatter y ofrezca estos métodos:
#   - resumen() -> dict con conteo por nivel
#   - errores() -> lista de los mensajes de nivel ERROR/CRITICAL
#   - duracion_total() -> suma de campos duracion_seg si existen
# Pruébalo con el archivo etl_structured.jsonl generado en la Parte C.

# TODO:
