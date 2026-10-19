"""
Módulo del Paradigma Voraz (Greedy).
Implementación manual de:
1. Heurística del Vecino Más Cercano (Nearest Neighbor) para TSP de reparto.
2. Asignación voraz de pedidos de emergencia al repartidor más próximo.

Prohibido el uso de librerías externas de optimización.
"""

import time
from typing import Dict, List, Optional, Set, Tuple
from core.grafo import obtener_matriz_distancias
from core.modelos import Grafo, Pedido, Repartidor, Ruta


def vecino_mas_cercano(
    nodo_inicio_id: str,
    pedidos: List[Pedido],
    grafo: Grafo,
    retornar_al_inicio: bool = False,
) -> Ruta:
    """
    Construye una ruta de reparto aplicando la heurística voraz del Vecino Más Cercano.

    Paradigma: Greedy (Voraz).
    Idea: En cada paso, desde la posición actual, el repartidor selecciona y visita
          el pedido pendiente con menor distancia dirigida de red (matriz de Dijkstra),
          sin reevaluar decisiones pasadas ni considerar el impacto global futuro.

    Complejidad Temporal:
      - O(n²) donde n es el número de pedidos.
      - Justificación: En la iteración 1 se evalúan n candidatos; en la 2, (n-1)...
        Suma: n + (n-1) + ... + 1 = n(n+1)/2 = O(n²).
    
      - Supone la matriz de distancias de red ya calculada (consulta O(1)). Esa matriz
        se obtiene una sola vez con V ejecuciones de Dijkstra: O(V·(V+E) log V), y se
        reutiliza en todas las llamadas mientras no cambie el estado de las calles.

    Complejidad Espacial:
      - O(n) para mantener el conjunto de pedidos visitados y la secuencia de la ruta.

    :param nodo_inicio_id: ID del nodo de partida (e.g. 'N01').
    :param pedidos: Subconjunto de pedidos a entregar.
    :param grafo: Red vial de Cusco.
    :param retornar_al_inicio: Si es True, añade el tramo final de regreso al inicio.
    :return: Objeto Ruta con la secuencia de nodos, distancia total y tiempo de cómputo.
    """
    t_inicio = time.perf_counter()

    if not pedidos:
        return Ruta(
            secuencia_nodos=[nodo_inicio_id],
            pedidos_cubiertos=[],
            distancia_total_m=0.0,
            algoritmo_utilizado="Greedy (Vecino Cercano)",
            tiempo_computo_ms=0.0,
        )

    if nodo_inicio_id not in grafo.nodos:
        raise ValueError(f"El nodo inicial {nodo_inicio_id!r} no existe.")
    matriz = obtener_matriz_distancias(grafo)

    pendientes = list(pedidos)
    secuencia_nodos = [nodo_inicio_id]
    pedidos_atendidos = []
    distancia_acumulada = 0.0
    nodo_actual_id = nodo_inicio_id

    while pendientes:
        mejor_dist = float("inf")
        mejor_idx = -1

        for idx, p in enumerate(pendientes):
            if p.nodo_id not in grafo.nodos:
                raise ValueError(f"El nodo del pedido {p.id!r} no existe en el grafo.")
            dist = matriz[nodo_actual_id][p.nodo_id]
            if dist < mejor_dist:
                mejor_dist = dist
                mejor_idx = idx

        if mejor_idx == -1 or mejor_dist == float("inf"):
            raise ValueError(
                f"No hay camino dirigido desde {nodo_actual_id} a ningún pedido pendiente."
            )
        siguiente_pedido = pendientes.pop(mejor_idx)
        distancia_acumulada += mejor_dist
        secuencia_nodos.append(siguiente_pedido.nodo_id)
        pedidos_atendidos.append(siguiente_pedido.id)
        nodo_actual_id = siguiente_pedido.nodo_id

    if retornar_al_inicio and secuencia_nodos:
        dist_retorno = matriz[nodo_actual_id][nodo_inicio_id]
        if dist_retorno == float("inf"):
            raise ValueError(
                f"No existe camino dirigido de retorno desde {nodo_actual_id} a {nodo_inicio_id}."
            )
        distancia_acumulada += dist_retorno
        secuencia_nodos.append(nodo_inicio_id)

    t_fin = time.perf_counter()
    tiempo_ms = (t_fin - t_inicio) * 1000.0

    return Ruta(
        secuencia_nodos=secuencia_nodos,
        pedidos_cubiertos=pedidos_atendidos,
        distancia_total_m=round(distancia_acumulada, 2),
        algoritmo_utilizado="Greedy (Vecino Cercano)",
        tiempo_computo_ms=round(tiempo_ms, 3),
    )


def asignar_pedido_emergencia(
    pedido_urgente: Pedido,
    repartidores: List[Repartidor],
    grafo: Grafo,
) -> Tuple[Optional[Repartidor], float, float]:
    """
    Asigna un pedido urgente al repartidor con menor distancia dirigida por calles.

    Paradigma: Greedy (Voraz).
    Idea: Compara la distancia de red desde la posición actual de cada repartidor hasta
          el nodo del pedido y elige el mínimo entre quienes tienen capacidad disponible.

    Complejidad Temporal:
      - O(R) donde R es la cantidad de repartidores: una comparación por repartidor.
        (Con los 3 repartidores de los datos de prueba son 3 comparaciones, pero la
        complejidad sigue siendo lineal en R.)
    Complejidad Espacial:
      - O(1) variables escalares.

    :param pedido_urgente: Pedido con prioridad 1.
    :param repartidores: Lista de repartidores activos.
    :param grafo: Grafo de Cusco.
    :return: Tupla con (Repartidor_seleccionado, distancia_m, tiempo_ms).
    """
    t_inicio = time.perf_counter()

    mejor_repartidor = None
    menor_distancia = float("inf")
    matriz = obtener_matriz_distancias(grafo)

    for rep in repartidores:
        # Verificar capacidad de carga
        if rep.cap_peso_kg < pedido_urgente.peso_kg or rep.cap_vol_l < pedido_urgente.volumen_l:
            continue

        pos_rep_id = rep.nodo_actual_id or rep.nodo_inicio_id
        if pos_rep_id not in grafo.nodos or pedido_urgente.nodo_id not in grafo.nodos:
            continue

        dist = matriz[pos_rep_id][pedido_urgente.nodo_id]
        if dist < menor_distancia:
            menor_distancia = dist
            mejor_repartidor = rep

    t_fin = time.perf_counter()
    tiempo_ms = (t_fin - t_inicio) * 1000.0

    return mejor_repartidor, round(menor_distancia, 2), round(tiempo_ms, 3)


def mochila_voraz_por_densidad(
    pedidos: List[Pedido], capacidad_peso_kg: float
) -> Tuple[float, List[Pedido]]:
    """
    Heurística voraz para la mochila: toma los pedidos de mayor valor por kg
    (valor/peso) mientras quepan. Sirve de contraste con la Mochila 0/1 por PD.

    Paradigma: Greedy. No garantiza el óptimo en la mochila 0/1 (sí en la fraccionaria).
    Contraejemplo clásico: pesos (1, 2, 3), valores (15, 10, 30), W = 4: el voraz toma
    1 y 2 (valor 25) y luego no cabe el 3; el óptimo es 1 + 3 (valor 45).

    Complejidad Temporal: O(n log n) por el Merge Sort manual + O(n) del recorrido.
    Complejidad Espacial: O(n).
    """
    from core.estructuras import merge_sort

    def _densidad(p: Pedido) -> float:
        return p.valor_soles / p.peso_kg if p.peso_kg > 0 else float("inf")

    ordenados = merge_sort(pedidos, key=_densidad, reverse=True)
    elegidos: List[Pedido] = []
    carga = 0.0
    valor = 0.0
    for p in ordenados:
        if carga + p.peso_kg <= capacidad_peso_kg + 1e-9:
            elegidos.append(p)
            carga += p.peso_kg
            valor += p.valor_soles
    return valor, elegidos
