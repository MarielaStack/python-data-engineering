# Python para Ingeniería de Datos

## Módulo 1 — Básico

| # | Archivo | Temas |
|---|---------|-------|
| 1 | `modulo_01_basico/01_variables.py` | Tipos de datos, casting, asignación múltiple |
| 2 | `modulo_01_basico/02_strings.py` | Métodos de string, slicing, f-strings |
| 3 | `modulo_01_basico/03_listas_tuplas.py` | Listas, tuplas, list comprehensions |
| 4 | `modulo_01_basico/04_diccionarios.py` | Dicts, dict comprehensions, listas de dicts |
| 5 | `modulo_01_basico/05_condicionales.py` | if/elif/else, truthy/falsy, validación ETL |
| 6 | `modulo_01_basico/06_bucles.py` | for, while, enumerate, zip, batch processing |
| 7 | `modulo_01_basico/07_funciones.py` | Funciones, *args/**kwargs, lambda, map/filter |

## Módulo 2 — Intermedio

| # | Archivo | Temas |
|---|---------|-------|
| 1 | `modulo_02_intermedio/01_manejo_errores.py` | try/except/finally, raise, excepciones personalizadas, decorador |
| 2 | `modulo_02_intermedio/02_archivos_csv_json.py` | csv, json stdlib, lectura/escritura, tipos, append seguro |
| 3 | `modulo_02_intermedio/03_pandas_intro.py` | Series, DataFrame, .info/.describe, read_csv/to_csv/Excel/JSON |
| 4 | `modulo_02_intermedio/04_pandas_transformaciones.py` | Filtros, groupby, merge/join, apply, map, fechas |
| 5 | `modulo_02_intermedio/05_pandas_etl.py` | Pipeline ETL completo: extract → transform → load + reporte calidad |

## Módulo 3 — Avanzado

| # | Archivo | Temas |
|---|---------|-------|
| 1 | `modulo_03_avanzado/01_sql_python.py` | sqlite3, INSERT/SELECT/UPDATE, pandas + SQL, upsert |
| 2 | `modulo_03_avanzado/02_apis_rest.py` | requests, paginación, auth, retry, POST/PUT/DELETE |
| 3 | `modulo_03_avanzado/03_logging_pipelines.py` | logging, handlers rotativos, JSON estructurado, decorador, context manager |
| 4 | `modulo_03_avanzado/04_funciones_avanzadas.py` | Generators, context managers (clase y @contextmanager), decoradores con parámetros, dataclasses |
| 5 | `modulo_03_avanzado/05_proyecto_integrador.py` | Pipeline completo: API → transform → SQLite → CSV/JSON + logging |

## Módulo 4 — Pipelines en Python

| # | Archivo | Temas |
|---|---------|-------|
| 1 | `modulo_04_pipelines/01_anatomia_pipeline.py` | SOURCE/TRANSFORM/SINK, batch vs streaming, pipeline como lista de pasos |
| 2 | `modulo_04_pipelines/02_pipeline_funcional.py` | pipe(), compose(), partial, map/filter/reduce, librería de transformaciones |
| 3 | `modulo_04_pipelines/03_pipeline_oop.py` | Clase Step, clase Pipeline, decorador @step, validación de esquema, branch |
| 4 | `modulo_04_pipelines/04_pipeline_resiliente.py` | Idempotencia, checkpointing, Dead Letter Queue, retry, Circuit Breaker |
| 5 | `modulo_04_pipelines/05_mini_orquestador.py` | DAG, orden topológico, dependencias >>, ejecución con contexto compartido |

## Cómo usar estas lecciones

1. Abre el archivo de la lección en tu editor.
2. Lee la sección de teoría (comentarios + ejemplos ejecutables).
3. Baja a la sección `EJERCICIOS`.
4. Completa cada `# TODO:` con tu código.
5. Ejecuta el script: `python nombre_leccion.py`
6. Si el resultado impreso coincide con lo esperado en el comentario, pasaste.
