# =============================================================================
# MÓDULO 4 - LECCIÓN 5: Mini Orquestador con DAG
# =============================================================================
# Los orquestadores reales (Airflow, Prefect, Dagster) manejan grafos de
# dependencias entre tareas. En esta lección construimos uno desde cero.
#
# Conceptos:
#   DAG          -> Directed Acyclic Graph (grafo acíclico dirigido)
#   Tarea (Task) -> unidad mínima de trabajo
#   Dependencia  -> "B no puede correr hasta que A termine"
#   Orden topológico -> orden de ejecución que respeta las dependencias
#   Run          -> una ejecución completa del DAG
# =============================================================================

import time
import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
LOG_DIR   = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)


# =============================================================================
# PARTE A — Qué es un DAG
# =============================================================================

# --- SECCIÓN 1: Grafo de dependencias ---
#
#  Ejemplo de DAG de un pipeline de ventas:
#
#   [extraer_api] ──┐
#                   ├──> [transformar] ──> [cargar_dw] ──> [notificar]
#   [extraer_csv] ──┘
#
# Reglas del DAG:
#   - Las flechas indican dependencia (A -> B significa "B depende de A")
#   - NO puede haber ciclos (A -> B -> C -> A rompería todo)
#   - Las tareas sin dependencias se pueden correr en paralelo
#   - Una tarea solo corre cuando TODOS sus padres terminaron con éxito


# =============================================================================
# PARTE B — Clase Task
# =============================================================================

# --- SECCIÓN 2: Representar una tarea ---

class EstadoTarea(Enum):
    PENDIENTE  = "pendiente"
    CORRIENDO  = "corriendo"
    EXITOSA    = "exitosa"
    FALLIDA    = "fallida"
    OMITIDA    = "omitida"   # se omite si algún padre falló


@dataclass
class ResultadoTarea:
    nombre:       str
    estado:       EstadoTarea
    duracion_seg: float = 0.0
    salida:       any   = None
    error:        str   = ""


class Task:
    """
    Unidad de trabajo del DAG.
    """

    def __init__(self, nombre: str, fn: Callable,
                 reintentos: int = 0, timeout_seg: float = None):
        self.nombre       = nombre
        self.fn           = fn
        self.reintentos   = reintentos
        self.timeout_seg  = timeout_seg
        self.dependencias: list["Task"] = []
        self.estado       = EstadoTarea.PENDIENTE
        self._resultado   = None

    def set_upstream(self, *tareas: "Task") -> "Task":
        """Define que esta tarea depende de las tareas dadas."""
        self.dependencias.extend(tareas)
        return self

    def __rshift__(self, otra: "Task") -> "Task":
        """Sobrecarga >> para sintaxis: tarea_a >> tarea_b"""
        otra.set_upstream(self)
        return otra

    def ejecutar(self, contexto: dict) -> ResultadoTarea:
        """Corre la función con reintentos."""
        self.estado = EstadoTarea.CORRIENDO
        t0 = time.perf_counter()

        for intento in range(self.reintentos + 1):
            try:
                salida = self.fn(contexto)
                duracion = round(time.perf_counter() - t0, 3)
                self.estado    = EstadoTarea.EXITOSA
                self._resultado = ResultadoTarea(
                    nombre=self.nombre, estado=self.estado,
                    duracion_seg=duracion, salida=salida
                )
                return self._resultado
            except Exception as e:
                if intento < self.reintentos:
                    print(f"    [RETRY {intento+1}/{self.reintentos}] {self.nombre}: {e}")
                    time.sleep(0.1 * (2 ** intento))
                else:
                    duracion = round(time.perf_counter() - t0, 3)
                    self.estado    = EstadoTarea.FALLIDA
                    self._resultado = ResultadoTarea(
                        nombre=self.nombre, estado=self.estado,
                        duracion_seg=duracion, error=str(e)
                    )
                    return self._resultado

    @property
    def padres_exitosos(self) -> bool:
        return all(t.estado == EstadoTarea.EXITOSA for t in self.dependencias)

    @property
    def tiene_padre_fallido(self) -> bool:
        return any(t.estado == EstadoTarea.FALLIDA for t in self.dependencias)

    def __repr__(self):
        return f"Task({self.nombre!r}, estado={self.estado.value})"


# =============================================================================
# PARTE C — Clase DAG
# =============================================================================

# --- SECCIÓN 3: Grafo que gestiona la ejecución ---

class DAG:
    """
    Grafo acíclico dirigido de tareas.
    Gestiona el orden de ejecución y el contexto compartido.
    """

    def __init__(self, nombre: str, descripcion: str = ""):
        self.nombre      = nombre
        self.descripcion = descripcion
        self.tareas: list[Task] = []

    def tarea(self, nombre: str, reintentos: int = 0):
        """Decorador para registrar una función como Task del DAG."""
        def decorator(fn: Callable) -> Task:
            t = Task(nombre, fn, reintentos=reintentos)
            self.tareas.append(t)
            return t
        return decorator

    def agregar(self, *tareas: Task) -> "DAG":
        self.tareas.extend(tareas)
        return self

    def _orden_topologico(self) -> list[Task]:
        """
        Ordena las tareas de forma que cada una aparece después
        de todas sus dependencias (algoritmo de Kahn).
        """
        # Calcular grado de entrada
        grado = {t.nombre: len(t.dependencias) for t in self.tareas}
        mapa  = {t.nombre: t for t in self.tareas}
        cola  = [t for t in self.tareas if grado[t.nombre] == 0]
        orden = []

        while cola:
            tarea = cola.pop(0)
            orden.append(tarea)
            # Reducir grado de las tareas que dependen de esta
            for candidata in self.tareas:
                if tarea in candidata.dependencias:
                    grado[candidata.nombre] -= 1
                    if grado[candidata.nombre] == 0:
                        cola.append(candidata)

        if len(orden) != len(self.tareas):
            raise ValueError("El DAG tiene ciclos — no es válido")

        return orden

    def ejecutar(self, contexto: dict = None) -> dict:
        """
        Ejecuta todas las tareas en orden topológico.
        Comparte un contexto mutable entre todas las tareas.
        """
        if contexto is None:
            contexto = {}

        orden = self._orden_topologico()
        resultados = {}

        print(f"\n{'='*55}")
        print(f"  DAG [{self.nombre}] — {len(orden)} tareas")
        print(f"  Orden: {' -> '.join(t.nombre for t in orden)}")
        print(f"{'='*55}")

        t_global = time.perf_counter()

        for tarea in orden:
            print(f"\n  [{tarea.nombre}]")

            if tarea.tiene_padre_fallido:
                tarea.estado = EstadoTarea.OMITIDA
                resultados[tarea.nombre] = ResultadoTarea(
                    nombre=tarea.nombre, estado=EstadoTarea.OMITIDA
                )
                print(f"    OMITIDA (padre fallido)")
                continue

            resultado = tarea.ejecutar(contexto)
            resultados[tarea.nombre] = resultado

            icono = "OK" if resultado.estado == EstadoTarea.EXITOSA else "FAIL"
            print(f"    {icono} | {resultado.duracion_seg}s"
                  + (f" | error: {resultado.error}" if resultado.error else ""))

        duracion_total = round(time.perf_counter() - t_global, 3)
        exitosas = sum(1 for r in resultados.values() if r.estado == EstadoTarea.EXITOSA)

        print(f"\n{'='*55}")
        print(f"  DAG [{self.nombre}] completado en {duracion_total}s")
        print(f"  Exitosas={exitosas} / Total={len(orden)}")
        print(f"{'='*55}")

        return {
            "dag":           self.nombre,
            "duracion_seg":  duracion_total,
            "tareas":        len(orden),
            "exitosas":      exitosas,
            "resultados":    {k: v.estado.value for k, v in resultados.items()},
            "contexto_final": contexto,
        }

    def visualizar(self):
        """Imprime una representación ASCII del grafo."""
        print(f"\nDAG: {self.nombre}")
        for tarea in self.tareas:
            if not tarea.dependencias:
                print(f"  [SOURCE] {tarea.nombre}")
            else:
                padres = ", ".join(p.nombre for p in tarea.dependencias)
                print(f"  {padres} --> {tarea.nombre}")


# =============================================================================
# PARTE D — Ejemplo completo: pipeline de ventas con DAG
# =============================================================================

# --- SECCIÓN 4: DAG de ventas ---

dag = DAG("pipeline_ventas_diario", "ETL diario de ventas desde API y CSV")

@dag.tarea("extraer_api", reintentos=2)
def extraer_api(ctx: dict):
    print("    Descargando usuarios desde API...")
    time.sleep(0.05)   # simula I/O
    ctx["usuarios"] = [
        {"id": 1, "nombre": "Juan",  "region": "norte"},
        {"id": 2, "nombre": "Maria", "region": "sur"},
    ]
    return f"{len(ctx['usuarios'])} usuarios"

@dag.tarea("extraer_csv")
def extraer_csv(ctx: dict):
    print("    Leyendo ventas.csv...")
    time.sleep(0.03)
    ctx["ventas"] = [
        {"id": 1, "usuario_id": 1, "monto": 1200.0},
        {"id": 2, "usuario_id": 2, "monto": 850.0},
        {"id": 3, "usuario_id": 1, "monto": 300.0},
    ]
    return f"{len(ctx['ventas'])} ventas"

@dag.tarea("transformar")
def transformar(ctx: dict):
    print("    Enriqueciendo ventas con usuarios...")
    usuarios = {u["id"]: u for u in ctx["usuarios"]}
    ctx["ventas_enriquecidas"] = [
        {**v, "nombre": usuarios[v["usuario_id"]]["nombre"],
              "region": usuarios[v["usuario_id"]]["region"]}
        for v in ctx["ventas"]
        if v["usuario_id"] in usuarios
    ]
    return f"{len(ctx['ventas_enriquecidas'])} filas enriquecidas"

@dag.tarea("cargar_dw")
def cargar_dw(ctx: dict):
    print("    Cargando en data warehouse...")
    time.sleep(0.04)
    ctx["filas_cargadas"] = len(ctx["ventas_enriquecidas"])
    return f"{ctx['filas_cargadas']} filas cargadas"

@dag.tarea("generar_reporte")
def generar_reporte(ctx: dict):
    print("    Generando reporte...")
    total = sum(v["monto"] for v in ctx["ventas_enriquecidas"])
    ctx["reporte"] = {"total_ventas": total, "filas": ctx["filas_cargadas"]}
    return ctx["reporte"]

# Definir dependencias con >>
extraer_api >> transformar
extraer_csv >> transformar
transformar >> cargar_dw >> generar_reporte

# Visualizar y ejecutar
dag.visualizar()
resultado = dag.ejecutar()

print("\nContexto final:")
for k, v in resultado["contexto_final"].items():
    print(f"  {k}: {v}")


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# Crea un DAG llamado "pipeline_logs" con estas 4 tareas y sus dependencias:
#   extraer_logs  -> parsear_logs -> filtrar_errores -> guardar_resumen
# Cada tarea debe modificar el contexto. Al final imprime el contexto final.

# TODO:


# EJ-2
# Agrega al DAG un método `ejecutar_desde(nombre_tarea, contexto)` que
# permita reejecutar el DAG desde una tarea específica (ignorando las anteriores).
# Útil para reanudar un DAG que falló a la mitad.

# TODO:


# EJ-3
# Implementa detección de ciclos en DAG._orden_topologico().
# Si el grafo tiene un ciclo (A depende de B y B depende de A),
# debe lanzar un ValueError descriptivo indicando cuál es el ciclo.
# Pruébalo creando un DAG con ciclo y verificando el error.

# TODO:


# EJ-4
# Agrega a DAG la capacidad de guardar el historial de ejecuciones en JSON:
#   dag.guardar_historial("historial_dag.json")
# El historial debe acumular runs anteriores.
# Corre el DAG 2 veces y verifica que el historial tiene 2 entradas.

# TODO:


# EJ-5 (desafío final del módulo)
# Construye un orquestador que ejecute múltiples DAGs en secuencia según
# un plan de ejecución diario:
#
#   plan = [
#       {"hora": "06:00", "dag": dag_ventas},
#       {"hora": "07:00", "dag": dag_inventario},
#       {"hora": "08:00", "dag": dag_reporte},
#   ]
#
# Implementa `Orquestador(plan)` con:
#   - run_all(): ejecuta todos los DAGs del plan en orden
#   - run_dag(nombre): ejecuta solo el DAG con ese nombre
#   - estado(): devuelve dict con el estado de cada DAG
#
# Simula que dag_inventario falla y verifica que dag_reporte igual se intenta.

# TODO:
