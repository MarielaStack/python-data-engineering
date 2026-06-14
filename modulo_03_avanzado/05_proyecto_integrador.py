# =============================================================================
# MÓDULO 3 - LECCIÓN 5: Proyecto Integrador
# =============================================================================
# Pipeline completo que integra todo el curso:
#
#   [MOD 1] variables, strings, listas, dicts, condicionales, bucles, funciones
#   [MOD 2] manejo de errores, CSV/JSON, pandas ETL
#   [MOD 3] SQL, APIs REST, logging, generators, context managers, dataclasses
#
# Escenario: pipeline diario de retail que:
#   1. EXTRAE  usuarios desde API pública (JSONPlaceholder)
#   2. EXTRAE  ventas desde CSV
#   3. TRANSFORMA y limpia los datos
#   4. CARGA   en SQLite (data warehouse local)
#   5. GENERA  reporte de calidad JSON
#   6. LOGGEA  cada etapa con timestamps y métricas
#
# Ejecutar: python 05_proyecto_integrador.py
# =============================================================================

import csv
import json
import logging
import logging.handlers
import os
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Generator, Optional

import requests
import pandas as pd


# =============================================================================
# CONFIGURACION
# =============================================================================

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "datos")
LOG_DIR    = os.path.join(BASE_DIR, "logs")
OUTPUT_DIR = os.path.join(DATA_DIR, "proyecto_output")

for d in [DATA_DIR, LOG_DIR, OUTPUT_DIR]:
    os.makedirs(d, exist_ok=True)

DB_PATH  = os.path.join(DATA_DIR, "retail_dw.db")
API_BASE = "https://jsonplaceholder.typicode.com"


# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class ConfigPipeline:
    nombre:          str
    version:         str  = "1.0.0"
    lote_tamanio:    int  = 500
    max_reintentos:  int  = 3
    timeout_api_seg: int  = 10
    etiquetas:       list = field(default_factory=list)


@dataclass
class ResultadoEtapa:
    etapa:        str
    filas_in:     int   = 0
    filas_out:    int   = 0
    filas_error:  int   = 0
    duracion_seg: float = 0.0
    ok:           bool  = True
    mensaje:      str   = ""


@dataclass
class ReporteCalidad:
    pipeline:        str
    timestamp:       str
    etapas:          list  = field(default_factory=list)
    total_filas_in:  int   = 0
    total_filas_out: int   = 0
    total_errores:   int   = 0
    tasa_error_pct:  float = 0.0
    ok:              bool  = True


# =============================================================================
# LOGGING
# =============================================================================

def _crear_logger(nombre: str) -> logging.Logger:
    log = logging.getLogger(nombre)
    log.setLevel(logging.DEBUG)
    if log.handlers:
        return log
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    fh = logging.handlers.RotatingFileHandler(
        os.path.join(LOG_DIR, "proyecto.log"),
        maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    log.addHandler(ch)
    log.addHandler(fh)
    return log

log = _crear_logger("pipeline.retail")


# =============================================================================
# UTILIDADES
# =============================================================================

@contextmanager
def cronometrar(nombre: str):
    t0 = time.perf_counter()
    try:
        yield
    finally:
        log.debug(f"[TIMER] {nombre}: {time.perf_counter() - t0:.3f}s")


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


def get_api(url: str, params: dict = None, timeout: int = 10,
            max_reintentos: int = 3) -> Optional[list]:
    for intento in range(1, max_reintentos + 1):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as e:
            if intento == max_reintentos:
                log.error(f"GET fallido tras {max_reintentos} intentos: {url} - {e}")
                return None
            log.warning(f"Reintento {intento}/{max_reintentos}: {e}")
            time.sleep(0.5 * intento)


def leer_csv_lotes(ruta: str, lote: int = 500) -> Generator:
    with open(ruta, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        buf = []
        for fila in reader:
            buf.append(fila)
            if len(buf) == lote:
                yield buf
                buf = []
        if buf:
            yield buf


# =============================================================================
# PASO 0 - Generar CSV de ejemplo
# =============================================================================

def generar_ventas_csv(ruta: str, n: int = 50):
    import random
    productos = ["arroz", "leche", "aceite", "azucar", "sal", "harina"]
    regiones  = ["norte", "sur", "este", "oeste"]
    random.seed(42)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        campos = ["id","fecha","producto","region","cantidad","precio","vendedor_id"]
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for i in range(1, n + 1):
            precio = round(random.uniform(3, 30), 2)
            w.writerow({
                "id":          i,
                "fecha":       f"2024-0{random.randint(1,3)}-{random.randint(1,28):02d}",
                "producto":    random.choice(productos),
                "region":      random.choice(regiones),
                "cantidad":    random.randint(10, 300),
                "precio":      precio if random.random() > 0.05 else "ERROR",
                "vendedor_id": f"V0{random.randint(1,5)}",
            })
    log.info(f"CSV generado: {n} filas en {os.path.basename(ruta)}")


CSV_VENTAS = os.path.join(DATA_DIR, "ventas_proyecto.csv")
generar_ventas_csv(CSV_VENTAS, n=50)


# =============================================================================
# INICIALIZAR DATA WAREHOUSE
# =============================================================================

def inicializar_dw(db_path: str):
    with conexion_sqlite(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id      INTEGER PRIMARY KEY,
                nombre  TEXT,
                email   TEXT,
                empresa TEXT
            );
            CREATE TABLE IF NOT EXISTS ventas (
                id          INTEGER PRIMARY KEY,
                fecha       TEXT,
                producto    TEXT,
                region      TEXT,
                cantidad    INTEGER,
                precio      REAL,
                total       REAL,
                vendedor_id TEXT,
                cargado_en  TEXT
            );
            CREATE TABLE IF NOT EXISTS ejecuciones (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline     TEXT,
                timestamp    TEXT,
                filas_in     INTEGER,
                filas_out    INTEGER,
                errores      INTEGER,
                ok           INTEGER,
                detalle_json TEXT
            );
        """)
    log.info("[DW] Esquema inicializado")


inicializar_dw(DB_PATH)


# =============================================================================
# EXTRACT
# =============================================================================

def extraer_usuarios(cfg: ConfigPipeline) -> ResultadoEtapa:
    etapa = ResultadoEtapa(etapa="extract_usuarios")
    log.info("[EXTRACT] Descargando usuarios desde API...")
    t0 = time.perf_counter()
    datos = get_api(f"{API_BASE}/users", timeout=cfg.timeout_api_seg,
                    max_reintentos=cfg.max_reintentos)
    etapa.duracion_seg = round(time.perf_counter() - t0, 3)
    if not datos:
        etapa.ok      = False
        etapa.mensaje = "API no respondio"
        return etapa
    etapa.filas_in = etapa.filas_out = len(datos)
    ruta = os.path.join(OUTPUT_DIR, "usuarios_raw.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2)
    log.info(f"[EXTRACT] Usuarios: {len(datos)} registros ({etapa.duracion_seg}s)")
    return etapa


def extraer_ventas_csv(cfg: ConfigPipeline) -> tuple:
    etapa = ResultadoEtapa(etapa="extract_ventas_csv")
    filas = []
    t0 = time.perf_counter()
    for lote in leer_csv_lotes(CSV_VENTAS, lote=cfg.lote_tamanio):
        etapa.filas_in += len(lote)
        filas.extend(lote)
    etapa.duracion_seg = round(time.perf_counter() - t0, 3)
    etapa.filas_out = len(filas)
    log.info(f"[EXTRACT] Ventas CSV: {etapa.filas_in} filas ({etapa.duracion_seg}s)")
    return etapa, filas


# =============================================================================
# TRANSFORM
# =============================================================================

def transformar_usuarios(ruta_raw: str) -> tuple:
    etapa = ResultadoEtapa(etapa="transform_usuarios")
    with open(ruta_raw, "r", encoding="utf-8") as f:
        datos = json.load(f)
    etapa.filas_in = len(datos)
    df = pd.json_normalize(datos)[["id", "name", "email", "company.name"]]
    df.columns    = ["id", "nombre", "email", "empresa"]
    df["nombre"]  = df["nombre"].str.strip()
    df["email"]   = df["email"].str.lower().str.strip()
    df["empresa"] = df["empresa"].str.strip()
    etapa.filas_out = len(df)
    log.info(f"[TRANSFORM] Usuarios: {etapa.filas_out} normalizados")
    return etapa, df


def transformar_ventas(filas_raw: list) -> tuple:
    etapa = ResultadoEtapa(etapa="transform_ventas")
    etapa.filas_in = len(filas_raw)
    df = pd.DataFrame(filas_raw)
    for col in ["producto", "region", "vendedor_id"]:
        df[col] = df[col].str.strip().str.lower()
    df["id"]       = pd.to_numeric(df["id"],       errors="coerce")
    df["cantidad"] = pd.to_numeric(df["cantidad"],  errors="coerce")
    df["precio"]   = pd.to_numeric(df["precio"],    errors="coerce")
    df["fecha"]    = pd.to_datetime(df["fecha"],    errors="coerce")
    mascara_ok = (
        df["fecha"].notna()    &
        df["cantidad"].notna() &
        df["precio"].notna()   &
        (df["cantidad"] > 0)   &
        (df["precio"] > 0)
    )
    df_err = df[~mascara_ok]
    df_ok  = df[mascara_ok].copy()
    etapa.filas_error = len(df_err)
    if len(df_err):
        df_err.to_csv(os.path.join(OUTPUT_DIR, "ventas_rechazadas.csv"), index=False)
        log.warning(f"[TRANSFORM] {len(df_err)} filas rechazadas")
    df_ok["total"]      = (df_ok["cantidad"] * df_ok["precio"]).round(2)
    df_ok["fecha"]      = df_ok["fecha"].dt.strftime("%Y-%m-%d")
    df_ok["cargado_en"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    etapa.filas_out = len(df_ok)
    log.info(f"[TRANSFORM] Ventas: {etapa.filas_out} validas, {etapa.filas_error} rechazadas")
    return etapa, df_ok


# =============================================================================
# LOAD
# =============================================================================

def cargar_dw(df_usuarios: pd.DataFrame, df_ventas: pd.DataFrame,
              cfg: ConfigPipeline) -> ResultadoEtapa:
    etapa = ResultadoEtapa(etapa="load")
    etapa.filas_in = len(df_usuarios) + len(df_ventas)
    t0 = time.perf_counter()
    with conexion_sqlite(DB_PATH) as conn:
        df_usuarios.to_sql("usuarios", conn, if_exists="replace", index=False)
        cols = ["id","fecha","producto","region","cantidad","precio","total","vendedor_id","cargado_en"]
        df_ventas[cols].to_sql("ventas", conn, if_exists="append", index=False)
    etapa.duracion_seg = round(time.perf_counter() - t0, 3)
    etapa.filas_out    = etapa.filas_in
    log.info(f"[LOAD] DW actualizado: {len(df_usuarios)} usuarios, {len(df_ventas)} ventas ({etapa.duracion_seg}s)")
    return etapa


# =============================================================================
# REPORTE
# =============================================================================

def generar_reporte(cfg: ConfigPipeline, etapas: list) -> ReporteCalidad:
    total_in  = sum(e.filas_in    for e in etapas)
    total_out = sum(e.filas_out   for e in etapas)
    total_err = sum(e.filas_error for e in etapas)
    tasa      = round(total_err / total_in * 100, 1) if total_in else 0.0
    reporte = ReporteCalidad(
        pipeline        = cfg.nombre,
        timestamp       = datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        etapas          = [e.__dict__ for e in etapas],
        total_filas_in  = total_in,
        total_filas_out = total_out,
        total_errores   = total_err,
        tasa_error_pct  = tasa,
        ok              = all(e.ok for e in etapas),
    )
    with conexion_sqlite(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO ejecuciones "
            "(pipeline,timestamp,filas_in,filas_out,errores,ok,detalle_json) "
            "VALUES (?,?,?,?,?,?,?)",
            (reporte.pipeline, reporte.timestamp, reporte.total_filas_in,
             reporte.total_filas_out, reporte.total_errores,
             int(reporte.ok), json.dumps(reporte.etapas)),
        )
    ts_safe  = reporte.timestamp.replace(":", "-")
    ruta_rep = os.path.join(OUTPUT_DIR, f"reporte_{ts_safe}.json")
    with open(ruta_rep, "w", encoding="utf-8") as f:
        json.dump(reporte.__dict__, f, indent=2, ensure_ascii=False)
    log.info(f"[REPORTE] Guardado: {os.path.basename(ruta_rep)}")
    return reporte


# =============================================================================
# PIPELINE PRINCIPAL
# =============================================================================

def ejecutar_pipeline(cfg: ConfigPipeline) -> ReporteCalidad:
    log.info("=" * 60)
    log.info(f"  PIPELINE [{cfg.nombre}] v{cfg.version} - INICIO")
    log.info("=" * 60)
    t_global = time.perf_counter()
    etapas = []

    e_usuarios                 = extraer_usuarios(cfg)
    e_ventas_csv, filas_ventas = extraer_ventas_csv(cfg)
    etapas.extend([e_usuarios, e_ventas_csv])

    if not e_usuarios.ok:
        log.error("Extraccion de usuarios fallo - abortando")
        return generar_reporte(cfg, etapas)

    e_tu, df_usuarios = transformar_usuarios(os.path.join(OUTPUT_DIR, "usuarios_raw.json"))
    e_tv, df_ventas   = transformar_ventas(filas_ventas)
    etapas.extend([e_tu, e_tv])

    e_load = cargar_dw(df_usuarios, df_ventas, cfg)
    etapas.append(e_load)

    reporte  = generar_reporte(cfg, etapas)
    duracion = time.perf_counter() - t_global
    estado   = "COMPLETADO" if reporte.ok else "CON ERRORES"

    log.info("=" * 60)
    log.info(f"  PIPELINE [{cfg.nombre}] {estado} | {duracion:.2f}s")
    log.info(f"  in={reporte.total_filas_in} | out={reporte.total_filas_out} | "
             f"errores={reporte.total_errores} | tasa={reporte.tasa_error_pct}%")
    log.info("=" * 60)
    return reporte


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    config = ConfigPipeline(
        nombre          = "retail_diario",
        version         = "1.0.0",
        lote_tamanio    = 25,
        max_reintentos  = 2,
        timeout_api_seg = 10,
        etiquetas       = ["produccion", "diario"],
    )
    reporte = ejecutar_pipeline(config)

    print("\n=== RESUMEN FINAL ===")
    print(f"  Pipeline  : {reporte.pipeline}")
    print(f"  Estado    : {'OK' if reporte.ok else 'CON ERRORES'}")
    print(f"  Filas in  : {reporte.total_filas_in}")
    print(f"  Filas out : {reporte.total_filas_out}")
    print(f"  Errores   : {reporte.total_errores} ({reporte.tasa_error_pct}%)")
    print(f"  Timestamp : {reporte.timestamp}")


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# El pipeline no descarga posts todavia.
# Agrega una etapa `extraer_posts(cfg)` que descargue /posts (100 registros),
# los guarde en posts_raw.json y retorne un ResultadoEtapa.
# Integra la etapa en ejecutar_pipeline().

# TODO:


# EJ-2
# Agrega validacion de calidad ANTES de cargar al DW:
#   - tasa_error_pct > 20%    -> detener pipeline, log CRITICAL
#   - tasa_error_pct 10%-20%  -> continuar, log WARNING
#   - tasa_error_pct < 10%    -> log INFO "Calidad OK"
# Prueba bajando el umbral en generar_ventas_csv de 0.05 a 0.20.

# TODO:


# EJ-3
# Agrega tabla `resumen_diario` al DW con:
#   fecha TEXT, region TEXT, total_ventas REAL, num_transacciones INTEGER
# Al final de cargar ventas, calcula con groupby y carga el resumen.

# TODO:


# EJ-4
# Agrega CLI con argparse:
#   python 05_proyecto_integrador.py --lote 100 --reintentos 5 --nombre "test"
# Modifica el bloque if __name__ == "__main__" para usar argparse.

import argparse
# TODO:


# EJ-5 (desafio final)
# Implementa `comparar_ejecuciones(db_path, n=5) -> pd.DataFrame` que lea
# las ultimas n filas de `ejecuciones`, calcule tasa_error_pct y el delta
# respecto a la ejecucion anterior. Si delta > 5 puntos, imprime una alerta.
# Corre el pipeline 2 veces y llama a comparar_ejecuciones().

# TODO:
