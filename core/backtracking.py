"""
Módulo de Backtracking con Poda (Búsqueda Exhaustiva Inteligente).
Encuentra todos los caminos simples entre dos nodos en la red vial de Cusco,
evitando calles cerradas/bloqueadas y podando ramas cuyo costo acumulado
iguale o supere la mejor distancia conocida (Branch and Bound).

Prohibido el uso de networkx o librerías de grafos prefabricadas.
"""

import time
from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple
from core.modelos import Grafo, Ruta


@dataclass
class ResultadoBacktracking:
    """Encapsula los resultados y métricas del árbol de exploración."""
    rutas_encontradas: List[Tuple[List[str], float]] = field(default_factory=list)
    ruta_optima: Optional[Tuple[List[str], float]] = None
    total_ramas_podadas: int = 0
    total_estados_visitados: int = 0
    tiempo_computo_ms: float = 0.0
    limite_alcanzado: bool = False


def buscar_rutas_backtracking(
    grafo: Grafo,
    origen_id: str,
    destino_id: str,
    max_rutas: int = 500,
    timeout_seg: float = 5.0,
    usar_poda: bool = True,
) -> ResultadoBacktracking:
    """
    Explora exhaustivamente todos los caminos simples entre origen y destino
    respetando el estado de las vías y aplicando poda por costo parcial.

    Paradigma: Backtracking (Vuelta Atrás con Poda).
    Idea: Realiza un recorrido en profundidad (DFS) en el espacio de estados.
          Al alcanzar un nodo, se evalúan sus vecinos transitables (activos).
          Si el costo acumulado ya supera o iguala la distancia de la mejor ruta
          encontrada hasta el momento, se poda la rama inmediatamente (corte).

    Dos modos (parámetro usar_poda):
      - usar_poda=False: búsqueda exhaustiva pura. Enumera TODOS los caminos simples
        (lo que pide literalmente el enunciado) y al final elige el más corto.
      - usar_poda=True (Branch & Bound): descarta una rama en cuanto su costo parcial
        iguala o supera la mejor ruta completa ya encontrada. Como los pesos son
        no negativos, el costo de una rama solo puede crecer al extenderla, así que una
        rama podada nunca puede terminar en una ruta más corta: la óptima se conserva.
        A cambio, rutas_encontradas solo contiene las rutas que fueron mejorando la cota.

    Complejidad Temporal:
      - Peor caso (grafo completo, sin poda): O(V!) caminos simples, cada uno de
        longitud O(V) al copiarlo -> O(V · V!).
      - Grafo disperso de grado medio b y caminos de largo d: O(b^d). La poda no cambia
        la cota del peor caso, pero reduce los estados visitados en la práctica
        (ver total_estados_visitados con y sin poda).

    Complejidad Espacial:
      - O(V) para la pila de recursión, el camino actual y el conjunto de visitados,
        más O(R · V) para guardar las R rutas encontradas.

    :param grafo: Grafo vial de Cusco.
    :param origen_id: ID del nodo inicial.
    :param destino_id: ID del nodo destino.
    :param max_rutas: Tope de seguridad de soluciones registradas.
    :param timeout_seg: Tiempo máximo de cálculo en segundos.
    :param usar_poda: True activa la poda por cota (Branch & Bound).
    :return: ResultadoBacktracking con caminos, ruta óptima y métricas.
    """
    t_inicio = time.perf_counter()

    if origen_id not in grafo.nodos or destino_id not in grafo.nodos:
        return ResultadoBacktracking()

    rutas_validas: List[Tuple[List[str], float]] = []
    mejor_distancia = float("inf")
    mejor_ruta = None

    contador_podas = 0
    contador_estados = 0
    limite_alcanzado = False

    def _dfs(
        u: str,
        camino: List[str],
        visitados: Set[str],
        costo_acumulado: float,
    ):
        nonlocal mejor_distancia, mejor_ruta, contador_podas, contador_estados, limite_alcanzado

        contador_estados += 1

        # Control de seguridad: timeout o número de rutas
        if len(rutas_validas) >= max_rutas or (time.perf_counter() - t_inicio) >= timeout_seg:
            limite_alcanzado = True
            return

        # PODA POR COTA: Si el camino parcial ya supera a la mejor ruta conocida
        if usar_poda and costo_acumulado >= mejor_distancia:
            contador_podas += 1
            return

        # Caso Base de Éxito: Llegamos al nodo destino
        if u == destino_id:
            ruta_copia = list(camino)
            rutas_validas.append((ruta_copia, round(costo_acumulado, 2)))
            if costo_acumulado < mejor_distancia:
                mejor_distancia = costo_acumulado
                mejor_ruta = (ruta_copia, round(costo_acumulado, 2))
            return

        # Exploración de vecinos transitables
        vecinos = grafo.obtener_vecinos_activos(u)
        for v, dist_uv in vecinos:
            if v not in visitados:
                # Paso Adelante
                visitados.add(v)
                camino.append(v)

                _dfs(v, camino, visitados, costo_acumulado + dist_uv)

                # Vuelta Atrás (Backtrack): Deshacer elección
                camino.pop()
                visitados.remove(v)

    # Iniciar búsqueda
    visitados_inicial: Set[str] = {origen_id}
    camino_inicial: List[str] = [origen_id]

    _dfs(origen_id, camino_inicial, visitados_inicial, 0.0)

    # Ordenar las rutas encontradas por distancia ascendente mediante sort manual
    from core.estructuras import quick_sort
    rutas_ordenadas = quick_sort(rutas_validas, key=lambda r: r[1])

    t_fin = time.perf_counter()
    tiempo_ms = (t_fin - t_inicio) * 1000.0

    return ResultadoBacktracking(
        rutas_encontradas=rutas_ordenadas,
        ruta_optima=mejor_ruta,
        total_ramas_podadas=contador_podas,
        total_estados_visitados=contador_estados,
        tiempo_computo_ms=round(tiempo_ms, 3),
        limite_alcanzado=limite_alcanzado,
    )
