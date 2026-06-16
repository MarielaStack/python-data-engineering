# =============================================================================
# MÓDULO 4 - LECCIÓN 3: Pipeline Orientado a Objetos
# =============================================================================
# Modelar el pipeline como clases permite:
#   - Registrar y nombrar cada paso
#   - Guardar métricas por etapa
#   - Validar esquemas de entrada/salida
#   - Pausar, reanudar y depurar el flujo
#   - Reutilizar pasos en distintos pipelines
#
# Patrón: Step -> Pipeline -> Runner
# =============================================================================

import time
from dataclasses import dataclass, field
from typing import Callable, Optional


# =============================================================================
# PARTE A — Clase Step
# =============================================================================

# --- SECCIÓN 1: Un paso con nombre y métricas ---

@dataclass
class MetricasPaso:
    filas_in:     int   = 0
    filas_out:    int   = 0
    duracion_seg: float = 0.0
    errores:      int   = 0
    ok:           bool  = True
    mensaje:      str   = ""


class Step:
    """
    Representa un paso del pipeline.
    Envuelve una función de transformación y registra métricas.
    """

    def __init__(self, nombre: str, fn: Callable, activo: bool = True):
        self.nombre  = nombre
        self.fn      = fn
        self.activo  = activo
        self.metricas = MetricasPaso()

    def ejecutar(self, datos: list) -> list:
        if not self.activo:
            print(f"  [SKIP] {self.nombre}")
            return datos

        self.metricas.filas_in = len(datos)
        t0 = time.perf_counter()
        try:
            resultado = self.fn(datos)
            self.metricas.filas_out    = len(resultado)
            self.metricas.duracion_seg = round(time.perf_counter() - t0, 4)
            self.metricas.ok           = True
            print(f"  [OK]  {self.nombre:30s} in={self.metricas.filas_in} "
                  f"out={self.metricas.filas_out} {self.metricas.duracion_seg}s")
            return resultado
        except Exception as e:
            self.metricas.ok      = False
            self.metricas.mensaje = str(e)
            self.metricas.duracion_seg = round(time.perf_counter() - t0, 4)
            print(f"  [ERR] {self.nombre:30s} {e}")
            raise

    def __repr__(self):
        return f"Step({self.nombre!r}, activo={self.activo})"


# Probar un Step aislado
step_norm = Step(
    nombre="normalizar_strings",
    fn=lambda datos: [{**r, "region": r["region"].lower().strip()} for r in datos]
)

test_datos = [{"id": 1, "region": " NORTE "}, {"id": 2, "region": "SUR"}]
resultado  = step_norm.ejecutar(test_datos)
print(f"  Resultado: {resultado}")
print(f"  Métricas: {step_norm.metricas}\n")


# =============================================================================
# PARTE B — Clase Pipeline
# =============================================================================

# --- SECCIÓN 2: Pipeline que encadena Steps ---

class Pipeline:
    """
    Encadena una lista de Steps y gestiona la ejecución completa.
    """

    def __init__(self, nombre: str):
        self.nombre  = nombre
        self.pasos:  list[Step] = []
        self._datos: Optional[list] = None

    def agregar(self, paso: Step) -> "Pipeline":
        """Agrega un paso. Retorna self para encadenamiento fluido."""
        self.pasos.append(paso)
        return self

    def step(self, nombre: str, activo: bool = True):
        """
        Decorador para registrar una función como paso del pipeline.

        Uso:
            @pipeline.step("mi_paso")
            def mi_paso(datos):
                ...
        """
        def decorator(fn: Callable) -> Callable:
            self.agregar(Step(nombre, fn, activo=activo))
            return fn
        return decorator

    def run(self, datos: list) -> list:
        """Ejecuta todos los pasos en orden."""
        print(f"\n{'='*50}")
        print(f"  PIPELINE [{self.nombre}] — {len(self.pasos)} pasos")
        print(f"{'='*50}")
        t_global = time.perf_counter()

        self._datos = datos
        for paso in self.pasos:
            self._datos = paso.ejecutar(self._datos)

        duracion = round(time.perf_counter() - t_global, 3)
        print(f"\n  Completado en {duracion}s — {len(self._datos)} filas finales")
        return self._datos

    def reporte(self) -> dict:
        """Devuelve métricas de todos los pasos."""
        return {
            "pipeline": self.nombre,
            "pasos": [
                {
                    "nombre":       p.nombre,
                    "activo":       p.activo,
                    "filas_in":     p.metricas.filas_in,
                    "filas_out":    p.metricas.filas_out,
                    "duracion_seg": p.metricas.duracion_seg,
                    "ok":           p.metricas.ok,
                }
                for p in self.pasos
            ],
        }

    def desactivar_paso(self, nombre: str):
        """Desactiva un paso por nombre (útil para debug)."""
        for p in self.pasos:
            if p.nombre == nombre:
                p.activo = False
                print(f"  [CONFIG] Paso '{nombre}' desactivado")
                return
        raise ValueError(f"Paso '{nombre}' no encontrado")


# --- Construir un pipeline con la clase ---

ventas_raw = [
    {"id": 1, "nombre": "  JUAN  ", "region": "NORTE", "cantidad": "100", "precio": "12.5"},
    {"id": 2, "nombre": "maria",    "region": "sur",   "cantidad": "-20", "precio": "8.0"},
    {"id": 3, "nombre": "PEDRO",    "region": "Este",  "cantidad": "80",  "precio": "abc"},
    {"id": 4, "nombre": "ANA",      "region": "norte", "cantidad": "150", "precio": "9.75"},
    {"id": 5, "nombre": "Luis",     "region": "SUR",   "cantidad": "200", "precio": "8.0"},
]

pl = Pipeline("ventas_diarias")

@pl.step("normalizar_texto")
def normalizar_texto(datos):
    return [{**r,
             "nombre": r["nombre"].strip().title(),
             "region": r["region"].strip().lower()}
            for r in datos]

@pl.step("convertir_tipos")
def convertir_tipos(datos):
    resultado = []
    for r in datos:
        try:
            resultado.append({**r,
                               "cantidad": int(r["cantidad"]),
                               "precio":   float(r["precio"])})
        except (ValueError, TypeError):
            pass
    return resultado

@pl.step("filtrar_invalidos")
def filtrar_invalidos(datos):
    return [r for r in datos if r["cantidad"] > 0 and r["precio"] > 0]

@pl.step("calcular_total")
def calcular_total(datos):
    return [{**r, "total": round(r["cantidad"] * r["precio"], 2)} for r in datos]

resultado = pl.run(ventas_raw)
print("\nReporte:")
import json
print(json.dumps(pl.reporte(), indent=2))


# =============================================================================
# PARTE C — Pipeline con validación de esquema
# =============================================================================

# --- SECCIÓN 3: Validar columnas requeridas antes de correr ---

class PipelineValidado(Pipeline):
    """
    Extiende Pipeline con validación de esquema
    antes de ejecutar el primer paso.
    """

    def __init__(self, nombre: str, columnas_requeridas: list = None):
        super().__init__(nombre)
        self.columnas_requeridas = columnas_requeridas or []

    def _validar_esquema(self, datos: list):
        if not datos:
            raise ValueError("Los datos de entrada están vacíos")
        primera_fila = datos[0]
        faltantes = [c for c in self.columnas_requeridas if c not in primera_fila]
        if faltantes:
            raise ValueError(f"Columnas requeridas faltantes: {faltantes}")
        print(f"  [SCHEMA] Validación OK — {len(self.columnas_requeridas)} columnas presentes")

    def run(self, datos: list) -> list:
        self._validar_esquema(datos)
        return super().run(datos)


pl_v = PipelineValidado("ventas_v2", columnas_requeridas=["id", "cantidad", "precio"])

@pl_v.step("agregar_total")
def agregar_total(datos):
    return [{**r, "total": r["cantidad"] * r["precio"]} for r in datos]

datos_validos = [{"id": 1, "cantidad": 100, "precio": 12.5}]
pl_v.run(datos_validos)

try:
    datos_invalidos = [{"id": 1, "monto": 100}]   # falta "cantidad" y "precio"
    pl_v.run(datos_invalidos)
except ValueError as e:
    print(f"  [SCHEMA ERROR] {e}")


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# Crea un Pipeline llamado "logs_etl" con estos 4 pasos usando el decorador @pl.step:
#   1. filtrar_errores:  solo logs con status >= 400
#   2. extraer_campos:   conservar solo endpoint, status, usuario
#   3. clasificar:       agregar "tipo" = "client_error" o "server_error"
#   4. ordenar:          ordenar por status descendente
# Pruébalo con los logs de la lección anterior.

logs = [
    {"id": 1, "endpoint": "/api/ventas",    "status": 200, "usuario": "u1"},
    {"id": 2, "endpoint": "/api/productos", "status": 404, "usuario": "u2"},
    {"id": 3, "endpoint": "/api/ventas",    "status": 500, "usuario": "u1"},
    {"id": 4, "endpoint": "/api/usuarios",  "status": 403, "usuario": "u3"},
    {"id": 5, "endpoint": "/api/reportes",  "status": 503, "usuario": "u1"},
]
# TODO:


# EJ-2
# Agrega a la clase Pipeline un método `resumen_metricas()` que imprima
# una tabla con: paso, filas_in, filas_out, pérdida(%), duración.
# Formato sugerido:
#   PASO                  | IN  | OUT | PÉRDIDA | DURACIÓN
#   normalizar_texto      | 5   | 5   | 0.0%    | 0.001s

# TODO: modifica Pipeline o crea subclase


# EJ-3
# Implementa `Pipeline.clonar(nombre_nuevo)` que cree un nuevo Pipeline
# con los mismos pasos pero métricas en cero.
# Úsalo para ejecutar el mismo pipeline sobre dos datasets distintos
# y compara los reportes.

# TODO:


# EJ-4
# Agrega a Step la capacidad de "modo dry-run":
#   step = Step("mi_paso", fn, dry_run=True)
# En dry-run, el paso NO transforma los datos (los pasa tal cual)
# pero SÍ loggea lo que hubiera hecho (cuántas filas afectaría).
# Útil para probar un pipeline sin modificar datos reales.

# TODO:


# EJ-5 (desafío)
# Implementa `Pipeline.branch(condicion, pipeline_a, pipeline_b)`:
# Divide los datos según la condición, corre pipeline_a sobre los que
# cumplen y pipeline_b sobre los que no, luego une los resultados.
# Agrega este método a la clase Pipeline y pruébalo dividiendo ventas
# por region=="norte" y procesando cada grupo con pasos distintos.

# TODO:
