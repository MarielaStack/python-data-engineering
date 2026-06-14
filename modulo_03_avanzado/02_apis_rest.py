# =============================================================================
# MÓDULO 3 - LECCIÓN 2: Consumir APIs REST
# =============================================================================
# pip install requests
#
# En datos: extraer desde APIs públicas/internas, webhooks, servicios de terceros.
# Patrones frecuentes: paginación, autenticación, retry, rate limiting.
#
# Esta lección usa la API pública https://jsonplaceholder.typicode.com
# (sin API key, siempre disponible) para los ejemplos.
# =============================================================================

import requests
import json
import time
import os
from typing import Optional

BASE_URL = "https://jsonplaceholder.typicode.com"
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")
os.makedirs(OUTPUT, exist_ok=True)


# =============================================================================
# PARTE A — GET básico
# =============================================================================

# --- A1: GET simple ---

response = requests.get(f"{BASE_URL}/posts/1")

print(f"Status code: {response.status_code}")      # 200 = OK
print(f"Content-Type: {response.headers['Content-Type']}")
print(f"Tamaño respuesta: {len(response.content)} bytes")

datos = response.json()    # parsea el JSON automáticamente
print(f"\nPost #1: {datos}")


# --- A2: Siempre verificar el status code ---

def get_seguro(url: str, **kwargs) -> Optional[dict]:
    """GET con manejo de errores HTTP."""
    try:
        resp = requests.get(url, timeout=10, **kwargs)
        resp.raise_for_status()   # lanza HTTPError si 4xx/5xx
        return resp.json()
    except requests.exceptions.HTTPError as e:
        print(f"[HTTP ERROR] {e}")
    except requests.exceptions.ConnectionError:
        print(f"[CONNECTION ERROR] No se pudo conectar a {url}")
    except requests.exceptions.Timeout:
        print(f"[TIMEOUT] La petición a {url} tardó demasiado")
    return None

post = get_seguro(f"{BASE_URL}/posts/5")
if post:
    print(f"\nTítulo: {post['title'][:50]}")

# probar con URL inválida
get_seguro(f"{BASE_URL}/posts/99999")


# --- A3: Query params ---

# /comments?postId=1  (filtrar comentarios del post 1)
comentarios = requests.get(
    f"{BASE_URL}/comments",
    params={"postId": 1},    # se convierte a ?postId=1
    timeout=10,
).json()
print(f"\nComentarios del post 1: {len(comentarios)}")


# =============================================================================
# PARTE B — Paginación
# =============================================================================

def paginar(base_url: str, endpoint: str, page_size: int = 10, max_paginas: int = 3) -> list:
    """
    Extrae datos paginados. Asume paginación con _page y _limit (JSONPlaceholder).
    Detiene cuando la página devuelve 0 resultados o se alcanza max_paginas.
    """
    todos = []
    pagina = 1

    while pagina <= max_paginas:
        print(f"  Descargando página {pagina}...")
        resp = requests.get(
            f"{base_url}/{endpoint}",
            params={"_page": pagina, "_limit": page_size},
            timeout=10,
        )
        resp.raise_for_status()
        datos = resp.json()

        if not datos:
            print("  Sin más datos")
            break

        todos.extend(datos)
        pagina += 1
        time.sleep(0.1)   # respetar el rate limiting

    return todos

print("\nPaginando posts...")
posts = paginar(BASE_URL, "posts", page_size=5, max_paginas=3)
print(f"Total descargados: {len(posts)}")


# =============================================================================
# PARTE C — Autenticación con headers
# =============================================================================

# Bearer token (patrón más común en APIs de datos)
TOKEN = "mi_token_secreto"   # en producción viene de env var

headers_auth = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# JSONPlaceholder ignora el token, pero el patrón es correcto
resp = requests.get(f"{BASE_URL}/users/1", headers=headers_auth, timeout=10)
usuario = resp.json()
print(f"\nUsuario autenticado: {usuario['name']} ({usuario['email']})")


# =============================================================================
# PARTE D — POST, PUT, DELETE
# =============================================================================

# POST — crear recurso
nuevo_post = {
    "title": "Pipeline de ventas Q1",
    "body":  "Resumen de ejecución del pipeline ETL del primer trimestre.",
    "userId": 1,
}
resp = requests.post(f"{BASE_URL}/posts", json=nuevo_post, timeout=10)
print(f"\nPOST status: {resp.status_code}")
print(f"Creado: {resp.json()}")

# PUT — actualizar recurso completo
actualizacion = {**nuevo_post, "title": "Pipeline de ventas Q1 — ACTUALIZADO"}
resp = requests.put(f"{BASE_URL}/posts/1", json=actualizacion, timeout=10)
print(f"\nPUT status: {resp.status_code}")

# PATCH — actualizar campo parcial
resp = requests.patch(f"{BASE_URL}/posts/1", json={"title": "Nuevo título"}, timeout=10)
print(f"PATCH status: {resp.status_code}")

# DELETE
resp = requests.delete(f"{BASE_URL}/posts/1", timeout=10)
print(f"DELETE status: {resp.status_code}")


# =============================================================================
# PARTE E — Retry con backoff exponencial
# =============================================================================

def get_con_retry(url: str, max_reintentos: int = 3, backoff: float = 1.0) -> Optional[dict]:
    """
    Reintenta en caso de error de red o 5xx.
    Espera backoff * 2^intento segundos entre reintentos.
    """
    for intento in range(max_reintentos):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code < 500:
                resp.raise_for_status()
                return resp.json()
            print(f"  [RETRY {intento+1}] Status {resp.status_code}, reintentando...")
        except (requests.ConnectionError, requests.Timeout) as e:
            print(f"  [RETRY {intento+1}] Error de red: {e}")

        espera = backoff * (2 ** intento)
        print(f"  Esperando {espera:.1f}s...")
        time.sleep(espera)

    print(f"[ERROR] Fallaron {max_reintentos} intentos para {url}")
    return None

resultado = get_con_retry(f"{BASE_URL}/todos/1")
if resultado:
    print(f"\nTodo: {resultado['title'][:50]}")


# =============================================================================
# PARTE F — Guardar respuesta de API a archivo
# =============================================================================

def extraer_y_guardar(endpoint: str, nombre_archivo: str):
    datos = paginar(BASE_URL, endpoint, page_size=10, max_paginas=2)
    ruta = os.path.join(OUTPUT, nombre_archivo)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
    print(f"\nGuardado {len(datos)} registros en {nombre_archivo}")
    return datos

usuarios = extraer_y_guardar("users", "usuarios_api.json")


# =============================================================================
# EJERCICIOS
# =============================================================================

# EJ-1
# Descarga todos los usuarios de GET /users (son 10 en JSONPlaceholder).
# Para cada usuario, extrae: id, name, email, company.name.
# Guarda como CSV con pandas.

# TODO:


# EJ-2
# Escribe una función `obtener_posts_usuario(user_id: int) -> list` que
# retorne todos los posts de un usuario usando el query param `userId`.
# Maneja los errores de red. Pruébala con user_id=1 y user_id=99.

# TODO:


# EJ-3
# Implementa `get_con_cache(url: str, cache: dict) -> dict`.
# Si la URL ya está en el cache, retorna el valor cacheado sin hacer la petición.
# Si no, hace el GET, guarda en cache y retorna.
# Prueba haciendo la misma petición 3 veces y verifica que solo se realiza 1 request.

cache_global = {}
# TODO: def get_con_cache(url, cache): ...


# EJ-4
# Crea un extractor paginado más robusto que detecte automáticamente
# el fin de la paginación usando el encabezado 'X-Total-Count' (si existe)
# o cuando la respuesta devuelva menos ítems que page_size.
# Pruébalo con el endpoint /posts.

# TODO:


# EJ-5 (desafío)
# Construye una función `pipeline_api_a_db(endpoint, db_path, tabla)`
# que:
#   1. Descargue todos los registros del endpoint (con paginación)
#   2. Normalice los campos (aplanar dicts anidados con _ como separador)
#      Ej: {"address": {"city": "X"}} -> {"address_city": "X"}
#   3. Guarde en una tabla SQLite usando pandas to_sql
#   4. Retorne el número de filas cargadas
#
# PISTA para aplanar: usa pd.json_normalize(lista_de_dicts)

# TODO:
