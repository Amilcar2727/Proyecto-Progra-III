"""Algoritmos manuales de caminos mínimos sobre el grafo de interés dirigido."""

import heapq
import math
from typing import Dict, List, Optional, Tuple

from core.modelos import Grafo


def reconstruir_camino(
    predecesores: Dict[str, Optional[str]], origen: str, destino: str
) -> List[str]:
    """Reconstruye el camino de Dijkstra; retorna [] si el destino es inalcanzable."""
    if origen == destino:
        return [origen]
    if destino not in predecesores or predecesores[destino] is None:
        return []

    camino = [destino]
    actual = destino
    while actual != origen:
        anterior = predecesores.get(actual)
        if anterior is None:
            return []
        camino.append(anterior)
        actual = anterior
    camino.reverse()
    return camino


def dijkstra(
    grafo: Grafo, origen: str
) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
    """
    Calcula distancias y predecesores desde un origen, ignorando aristas cerradas.

    Complejidad: O((V+E) log V) tiempo y O(V) espacio, usando heapq.
    """
    if origen not in grafo.nodos:
        raise ValueError(f"El nodo de origen {origen!r} no existe en el grafo.")

    distancias = {nodo_id: float("inf") for nodo_id in grafo.nodos}
    predecesores: Dict[str, Optional[str]] = {
        nodo_id: None for nodo_id in grafo.nodos
    }
    distancias[origen] = 0.0
    cola = [(0.0, origen)]

    while cola:
        distancia_actual, actual = heapq.heappop(cola)
        if distancia_actual != distancias[actual]:
            continue
        for vecino, longitud in grafo.obtener_vecinos_activos(actual):
            alternativa = distancia_actual + longitud
            if alternativa < distancias[vecino]:
                distancias[vecino] = alternativa
                predecesores[vecino] = actual
                heapq.heappush(cola, (alternativa, vecino))

    return distancias, predecesores


def calcular_matriz_distancias(
    grafo: Grafo,
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, List[str]]]]:
    """Calcula y guarda en el grafo las distancias y caminos mínimos entre pares."""
    matriz: Dict[str, Dict[str, float]] = {}
    caminos: Dict[str, Dict[str, List[str]]] = {}
    for origen in grafo.nodos:
        distancias, predecesores = dijkstra(grafo, origen)
        matriz[origen] = distancias
        caminos[origen] = {
            destino: reconstruir_camino(predecesores, origen, destino)
            for destino in grafo.nodos
        }
    grafo.matriz_distancias = matriz
    grafo.caminos_minimos = caminos
    return matriz, caminos


def obtener_matriz_distancias(grafo: Grafo) -> Dict[str, Dict[str, float]]:
    """Devuelve la matriz cacheada o la recalcula tras cambios en el grafo."""
    if grafo.matriz_distancias is None or grafo.caminos_minimos is None:
        calcular_matriz_distancias(grafo)
    return grafo.matriz_distancias


def obtener_camino_mas_corto(grafo: Grafo, origen: str, destino: str) -> List[str]:
    """Devuelve los nodos del camino dirigido más corto, o [] si no hay conexión."""
    obtener_matriz_distancias(grafo)
    if origen not in grafo.caminos_minimos or destino not in grafo.nodos:
        raise ValueError(f"Nodo de origen o destino inexistente: {origen!r}, {destino!r}.")
    return list(grafo.caminos_minimos[origen][destino])


def geometria_de_ruta(
    grafo: Grafo, secuencia_nodos: List[str]
) -> List[Tuple[float, float]]:
    """Concatena polilíneas dirigidas de la ruta mínima entre cada par de paradas."""
    puntos: List[Tuple[float, float]] = []
    for origen, destino in zip(secuencia_nodos, secuencia_nodos[1:]):
        camino = obtener_camino_mas_corto(grafo, origen, destino)
        if not camino:
            raise ValueError(f"No existe ruta activa desde {origen} hasta {destino}.")
        for u, v in zip(camino, camino[1:]):
            arista = grafo.adyacencia[u][v]
            if not arista.activa:
                raise RuntimeError(f"El arco {u}->{v} está cerrado dentro del camino cacheado.")
            if len(arista.geometria) < 2:
                raise ValueError(f"El arco {u}->{v} no tiene geometría vial.")
            if puntos and puntos[-1] == arista.geometria[0]:
                puntos.extend(arista.geometria[1:])
            else:
                puntos.extend(arista.geometria)
    return puntos


def matriz_para_nodos(grafo: Grafo, nodos: List[str]) -> List[List[float]]:
    """Extrae una submatriz ordenada para una lista de nodos, incluidos duplicados."""
    distancias = obtener_matriz_distancias(grafo)
    try:
        return [[distancias[u][v] for v in nodos] for u in nodos]
    except KeyError as error:
        raise ValueError(f"Nodo desconocido al extraer submatriz: {error.args[0]!r}.") from error


def validar_distancias(matriz: List[List[float]]) -> None:
    """Valida forma y pesos antes de entregar una matriz a Held-Karp."""
    n = len(matriz)
    if any(len(fila) != n for fila in matriz):
        raise ValueError("La matriz de distancias debe ser cuadrada.")
    if any(math.isnan(valor) or valor < 0 for fila in matriz for valor in fila):
        raise ValueError("Las distancias deben ser no negativas y no NaN.")
