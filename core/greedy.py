"""
Módulo del Paradigma Voraz (Greedy).
Implementación manual de:
1. Heurística del Vecino Más Cercano (Nearest Neighbor) para TSP de reparto.
2. Asignación voraz de pedidos de emergencia al repartidor más próximo.

Prohibido el uso de librerías externas de optimización.
"""

import time
from typing import Dict, List, Optional, Set, Tuple
from core.geo import distancia_haversine
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
          el pedido pendiente que se encuentre a la menor distancia geográfica (Haversine),
          sin reevaluar decisiones pasadas ni considerar el impacto global futuro.

    Complejidad Temporal:
      - O(n²) donde n es el número de pedidos.
      - Justificación: En la iteración 1 se evalúan n candidatos; en la 2, (n-1)...
        Suma: n + (n-1) + ... + 1 = n(n+1)/2 = O(n²).
    
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

    # Identificar coordenadas de inicio
    pos_actual_lat = grafo.nodos[nodo_inicio_id].lat
    pos_actual_lon = grafo.nodos[nodo_inicio_id].lon

    pendientes = list(pedidos)
    secuencia_nodos = [nodo_inicio_id]
    pedidos_atendidos = []
    distancia_acumulada = 0.0

    while pendientes:
        mejor_dist = float("inf")
        mejor_idx = -1

        for idx, p in enumerate(pendientes):
            dist = distancia_haversine(pos_actual_lat, pos_actual_lon, p.lat, p.lon)
            if dist < mejor_dist:
                mejor_dist = dist
                mejor_idx = idx

        siguiente_pedido = pendientes.pop(mejor_idx)
        distancia_acumulada += mejor_dist
        secuencia_nodos.append(siguiente_pedido.nodo_id)
        pedidos_atendidos.append(siguiente_pedido.id)

        pos_actual_lat = siguiente_pedido.lat
        pos_actual_lon = siguiente_pedido.lon

    if retornar_al_inicio and secuencia_nodos:
        nodo_fin = grafo.nodos[secuencia_nodos[-1]]
        nodo_ini = grafo.nodos[nodo_inicio_id]
        dist_retorno = distancia_haversine(nodo_fin.lat, nodo_fin.lon, nodo_ini.lat, nodo_ini.lon)
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
    Asigna un pedido urgente al repartidor disponible más cercano en distancia lineal.

    Paradigma: Greedy (Voraz).
    Idea: Compara la distancia desde la ubicación del pedido urgente hacia la posición
          actual de cada repartidor y selecciona el mínimo absoluto que tenga capacidad disponible.

    Complejidad Temporal:
      - O(R) donde R es la cantidad de repartidores. Como R <= 3 en este sistema, es O(1) efectivo.
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

    for rep in repartidores:
        # Verificar capacidad de carga
        if rep.cap_peso_kg < pedido_urgente.peso_kg or rep.cap_vol_l < pedido_urgente.volumen_l:
            continue

        pos_rep_nodo = grafo.nodos.get(rep.nodo_actual_id or rep.nodo_inicio_id)
        if not pos_rep_nodo:
            continue

        dist = distancia_haversine(
            pedido_urgente.lat, pedido_urgente.lon, pos_rep_nodo.lat, pos_rep_nodo.lon
        )
        if dist < menor_distancia:
            menor_distancia = dist
            mejor_repartidor = rep

    t_fin = time.perf_counter()
    tiempo_ms = (t_fin - t_inicio) * 1000.0

    return mejor_repartidor, round(menor_distancia, 2), round(tiempo_ms, 3)
