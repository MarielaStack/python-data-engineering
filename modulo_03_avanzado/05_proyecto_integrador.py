# =============================================================================
# MÓDULO 3 - LECCIÓN 5: Proyecto Integrador
# =============================================================================
# Este proyecto conecta TODO lo visto en los tres módulos:
#
#   API REST  ->  Transformación  ->  SQLite  ->  Reporte CSV/JSON
#       |               |                |               |
#   requests       pandas + dataclass  sqlite3       logging
#
# Escenario: sistema de seguimiento de usuarios y sus publicaciones
# extraídos de JSONPlaceholder (simula una fuente de datos externa).
#
# Pipeline completo:
#   1. Extraer usuarios y posts desde API (con reintentos)
#   2. Transformar y enriquecer (normalizar, calcular métricas por usuario)
#   3. Validar registros (separar válidos de rechazados)
#   4. Cargar en SQLite (upsert)
#   5. Generar reporte de calidad
#   6. Exportar resultados a CSV y JSON
#   7. Loggear cada etapa con duración y métricas
# =============================================================================

import requests
import sqlite3
import pandas as pd
import json
import logging
import logging.handlers
import time
import os
from dataclasses import dataclass, field
from contextlib import contextmanager
from functools import wraps
from datetime import datetime
from typing import Optional

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR  = os.path.join(BASE_DIR, "datos", "proyecto")
LOG_DIR     = os.path.join(BASE_DIR, "logs")
DB_PATH     = os.path.join(OUTPUT_DIR, "proyecto.db")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

API_BASE    = "https://jsonplaceholder.typicode.com"

CONFIG = {
    "max_reintentos":      3,
    "timeout_seg":         10,
    "max_tasa_rechazo":    20.0,   # % máximo de rechazos permitido
    "lote_db":             50,
}


# =============================================================================
# LOGGING
# =============================================================================

def _setup_logger(nombre: str) -> logging.Logger:
    log = logging.getLogger(nombre)
    log.setLevel(logging.DEBUG)
    if log.handlers:
        return log

    fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s", "%H:%M:%S")

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    log.addHandler(ch)

    fh = logging.handlers.RotatingFileHandler(
        os.path.join(LOG_DIR, "proyecto.log"),
        maxBytes=2 * 1024 * 1024, backupCount=2, encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    log.addHandler(fh)
    return log

log = _setup_logger("proyecto.etl")


# =============================================================================
# UTILIDADES
# =============================================================================

def cronometrar(func):
    """Decorador que loggea duración de cada etapa."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        log.info(f"▶ {func.__name__}")
        try:
            result = func(*args, **kwargs)
            log.info(f"✔ {func.__name__} ({time.perf_counter()-t0:.2f}s)")
            return result
        except Exception as e:
            log.error(f"✘ {func.__name__} ({time.perf_counter()-t0:.2f}s) — {e}", exc_info=True)
            raise
    return wrapper


@contextmanager
def conexion_sqlite(ruta: str):
    conn = sqlite3.connect(ruta)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class Usuario:
    id:       int
    nombre:   str
    email:    str
    ciudad:   str
    empresa:  str
    total_posts: int = 0

    @classmethod
    def desde_api(cls, raw: dict) -> "Usuario":
        return cls(
            id      = raw["id"],
            nombre  = raw["name"].strip(),
            email   = raw["email"].strip().lower(),
            ciudad  = raw.get("address", {}).get("city", "").strip(),
            empresa = raw.get("company", {}).get("name", "").strip(),
        )

    def es_valido(self) -> bool:
        return bool(self.nombre) and "@" in self.email


@dataclass
class Post:
    id:        int
    user_id:   int
    titulo:    str
    cuerpo:    str
    palabras:  int = field(init=False)

    def __post_init__(self):
        self.palabras = len(self.cuerpo.split())

    @classmethod
    def desde_api(cls, raw: dict) -> "Post":
        return cls(
            id      = raw["id"],
            user_id = raw["userId"],
            titulo  = raw["title"].strip(),
            cuerpo  = raw["body"].strip(),
        )


@dataclass
class ReporteCalidad:
    etapa:             str
    total_entrada:     int = 0
    total_validos:     int = 0
    total_rechazados:  int = 0
    duracion_seg:      float = 0.0
    errores:           list = field(default_factory=list)

    @property
    def tasa_rechazo(self) -> float:
        if self.total_entrada == 0:
            return 0.0
        return round(self.total_rechazados / self.total_entrada * 100, 1)

    def loggear(self):
        log.info(
            f"[{self.etapa}] entrada={self.total_entrada} "
            f"validos={self.total_validos} rechazados={self.total_rechazados} "
            f"({self.tasa_rechazo}%) {self.duracion_seg:.2f}s"
        )


# =============================================================================
# EXTRACCIÓN
# =============================================================================

def _get_con_retry(url: str, max_intentos: int, timeout: int) -> dict | list:
    for intento in range(1, max_intentos + 1):
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as e:
            log.warning(f"  Intento {intento}/{max_intentos} falló: {e}")
            if intento < max_intentos:
                time.sleep(2 ** (intento - 1))
    raise ConnectionError(f"No se pudo obtener {url} en {max_intentos} intentos")


@cronometrar
def extraer_usuarios() -> list[Usuario]:
    raw = _get_con_retry(
        f"{API_BASE}/users",
        CONFIG["max_reintentos"],
        CONFIG["timeout_seg"],
    )
    usuarios = [Usuario.desde_api(u) for u in raw]
    log.debug(f"  {len(usuarios)} usuarios crudos recibidos")
    return usuarios


@cronometrar
def extraer_posts() -> list[Post]:
    raw = _get_con_retry(
        f"{API_BASE}/posts",
        CONFIG["max_reintentos"],
        CONFIG["timeout_seg"],
    )
    posts = [Post.desde_api(p) for p in raw]
    log.debug(f"  {len(posts)} posts crudos recibidos")
    return posts


# =============================================================================
# TRANSFORMACIÓN
# =============================================================================

@cronometrar
def transformar(
    usuarios: list[Usuario],
    posts: list[Post],
) -> tuple[list[Usuario], list[Post], ReporteCalidad]:

    reporte = ReporteCalidad("transform")
    t0 = time.perf_counter()

    # Enriquecer usuarios con conteo de posts
    posts_por_user = {}
    for p in posts:
        posts_por_user[p.user_id] = posts_por_user.get(p.user_id, 0) + 1
    for u in usuarios:
        u.total_posts = posts_por_user.get(u.id, 0)

    # Validar
    usuarios_validos   = []
    usuarios_rechazados = []
    for u in usuarios:
        if u.es_valido():
            usuarios_validos.append(u)
        else:
            usuarios_rechazados.append(u)
            reporte.errores.append(f"Usuario {u.id}: inválido")

    reporte.total_entrada    = len(usuarios)
    reporte.total_validos    = len(usuarios_validos)
    reporte.total_rechazados = len(usuarios_rechazados)
    reporte.duracion_seg     = time.perf_counter() - t0
    reporte.loggear()

    return usuarios_validos, posts, reporte


# =============================================================================
# ESQUEMA Y CARGA
# =============================================================================

def _crear_esquema(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id          INTEGER PRIMARY KEY,
            nombre      TEXT NOT NULL,
            email       TEXT UNIQUE NOT NULL,
            ciudad      TEXT,
            empresa     TEXT,
            total_posts INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS posts (
            id        INTEGER PRIMARY KEY,
            user_id   INTEGER NOT NULL,
            titulo    TEXT NOT NULL,
            cuerpo    TEXT,
            palabras  INTEGER,
            FOREIGN KEY (user_id) REFERENCES usuarios(id)
        );
    """)


@cronometrar
def cargar(
    usuarios: list[Usuario],
    posts: list[Post],
) -> ReporteCalidad:

    reporte = ReporteCalidad("load")
    t0 = time.perf_counter()

    with conexion_sqlite(DB_PATH) as conn:
        _crear_esquema(conn)

        conn.executemany(
            """INSERT OR REPLACE INTO usuarios (id, nombre, email, ciudad, empresa, total_posts)
               VALUES (:id, :nombre, :email, :ciudad, :empresa, :total_posts)""",
            [u.__dict__ for u in usuarios],
        )

        conn.executemany(
            """INSERT OR REPLACE INTO posts (id, user_id, titulo, cuerpo, palabras)
               VALUES (:id, :user_id, :titulo, :cuerpo, :palabras)""",
            [p.__dict__ for p in posts],
        )

    reporte.total_entrada  = len(usuarios) + len(posts)
    reporte.total_validos  = len(usuarios) + len(posts)
    reporte.duracion_seg   = time.perf_counter() - t0
    reporte.loggear()
    return reporte


# =============================================================================
# REPORTE Y EXPORTACIÓN
# =============================================================================

@cronometrar
def generar_reporte(reportes: list[ReporteCalidad]):
    with conexion_sqlite(DB_PATH) as conn:
        df_usuarios = pd.read_sql("SELECT * FROM usuarios ORDER BY total_posts DESC", conn)
        df_posts    = pd.read_sql("""
            SELECT u.nombre, COUNT(p.id) as num_posts, AVG(p.palabras) as prom_palabras
            FROM posts p JOIN usuarios u ON p.user_id = u.id
            GROUP BY u.nombre ORDER BY num_posts DESC
        """, conn)

    # Exportar CSV
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    df_usuarios.to_csv(os.path.join(OUTPUT_DIR, f"usuarios_{ts}.csv"), index=False)
    df_posts.to_csv(os.path.join(OUTPUT_DIR, f"posts_resumen_{ts}.csv"), index=False)
    log.info(f"CSVs exportados en {OUTPUT_DIR}")

    # Reporte JSON de calidad
    reporte_final = {
        "timestamp": ts,
        "etapas": [
            {
                "etapa":            r.etapa,
                "total_entrada":    r.total_entrada,
                "total_validos":    r.total_validos,
                "total_rechazados": r.total_rechazados,
                "tasa_rechazo_pct": r.tasa_rechazo,
                "duracion_seg":     round(r.duracion_seg, 3),
            }
            for r in reportes
        ],
        "resumen": {
            "total_usuarios": len(df_usuarios),
            "usuario_mas_activo": df_usuarios.iloc[0]["nombre"] if len(df_usuarios) > 0 else None,
            "promedio_posts_por_usuario": round(df_usuarios["total_posts"].mean(), 1),
        },
    }

    ruta_rep = os.path.join(OUTPUT_DIR, f"reporte_calidad_{ts}.json")
    with open(ruta_rep, "w", encoding="utf-8") as f:
        json.dump(reporte_final, f, indent=2, ensure_ascii=False)

    log.info(f"Reporte de calidad: {os.path.basename(ruta_rep)}")
    return reporte_final


# =============================================================================
# ORQUESTADOR PRINCIPAL
# =============================================================================

def ejecutar_pipeline():
    log.info("=" * 60)
    log.info("PIPELINE PROYECTO INTEGRADOR — INICIO")
    log.info("=" * 60)

    t_inicio = time.perf_counter()
    reportes = []

    try:
        # 1. Extraer
        usuarios_raw = extraer_usuarios()
        posts_raw    = extraer_posts()

        # 2. Transformar
        usuarios_ok, posts_ok, rep_transform = transformar(usuarios_raw, posts_raw)
        reportes.append(rep_transform)

        # 3. Validar tasa de rechazo
        if rep_transform.tasa_rechazo > CONFIG["max_tasa_rechazo"]:
            raise ValueError(
                f"Tasa de rechazo {rep_transform.tasa_rechazo}% "
                f"supera el límite de {CONFIG['max_tasa_rechazo']}%"
            )

        # 4. Cargar
        rep_load = cargar(usuarios_ok, posts_ok)
        reportes.append(rep_load)

        # 5. Reporte
        reporte_final = generar_reporte(reportes)

    except Exception as e:
        log.critical(f"Pipeline abortado: {e}", exc_info=True)
        raise

    duracion_total = time.perf_counter() - t_inicio
    log.info(f"PIPELINE COMPLETADO en {duracion_total:.2f}s")
    log.info("=" * 60)
    return reporte_final


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    reporte = ejecutar_pipeline()
    print("\n=== RESUMEN FINAL ===")
    print(json.dumps(reporte["resumen"], indent=2, ensure_ascii=False))


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# Agrega una etapa de extracción de comentarios (GET /comments).
# Crea un dataclass `Comentario` con: id, post_id, nombre, email, cuerpo.
# Crea la tabla correspondiente en SQLite y cárgala en el pipeline.
# Incluye en el reporte final la métrica "promedio_comentarios_por_post".

# TODO:


# EJ-2
# Agrega validación de email en el dataclass Usuario usando una expresión
# regular básica: debe tener formato "algo@algo.algo".
# Cualquier usuario con email inválido debe ir a rechazados.
# Registra los rechazos con su motivo en el reporte.

import re
# TODO: modifica Usuario.es_valido() y prueba con emails inválidos


# EJ-3
# Implementa un modo "incremental" en cargar():
#   - Antes de insertar, consulta los ids ya existentes en la tabla usuarios.
#   - Solo inserta los que NO existen (INSERT, no REPLACE).
#   - Retorna en el reporte: filas_nuevas vs filas_ya_existentes.
#
# Ejecuta el pipeline dos veces y verifica que la segunda vez
# filas_nuevas == 0.

# TODO:


# EJ-4
# Agrega al reporte final una sección "alertas" que liste:
#   - Usuarios sin ciudad
#   - Usuarios con 0 posts
#   - Posts con menos de 5 palabras
# Cada alerta debe tener: tipo, descripcion, cantidad.

# TODO:


# EJ-5 (desafío final)
# Parametriza el pipeline con un archivo de configuración JSON externo:
#   pipeline_config.json:
#   {
#     "nombre": "proyecto_usuarios",
#     "api_base": "https://jsonplaceholder.typicode.com",
#     "endpoints": ["users", "posts", "comments"],
#     "max_reintentos": 3,
#     "max_tasa_rechazo": 20.0,
#     "output_dir": "datos/proyecto"
#   }
#
# Modifica `ejecutar_pipeline(config_path: str)` para que lea la config
# del JSON y ejecute solo los endpoints listados.
# Si el archivo no existe, usa valores por defecto.

# TODO:
