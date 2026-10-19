"""
Módulo de Divide y Vencerás (D&C) para Segmentación Espacial de Rutas.
Implementación manual de partición recursiva 2D por mediana alternada (Lat/Lon)
hasta umbral K, resolución de sub-rutas y combinación global.

Prohibido el uso de librerías externas de partición o k-d trees precompilados.
"""

import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from core.geo import distancia_haversine, centroide
from core.modelos import Grafo, Pedido, Ruta
from core.estructuras import quick_sort
from core.greedy import vecino_mas_cercano


@dataclass
class ZonaReparto:
    """Representa un clúster geográfico generado por la partición recursiva."""
    id_zona: int
    pedidos: List[Pedido]
    centroide: Tuple[float, float] = (0.0, 0.0)
    ruta_local: Optional[Ruta] = None


def particionar_pedidos_dyv(
    pedidos: List[Pedido],
    umbral_k: int = 5,
    profundidad: int = 0,
) -> List[List[Pedido]]:
    """
    Partición espacial recursiva de pedidos usando Divide y Vencerás.

    Paradigma: Divide y Vencerás (D&C).
    Idea: En cada nivel recursivo, si el tamaño es > K:
          1. DIVIDIR: Ordena los puntos alternando el eje (latitud en niveles pares,
             longitud en impares) usando QuickSort manual y corta por la mediana en 2 mitades.
          2. VENCER: Aplica la partición recursiva a la mitad izquierda y derecha.
          3. COMBINAR: Concatena las zonas resultantes de ambas ramas.

    Ecuación de Recurrencia:
      T(n) = 2 T(n/2) + O(n)   (donde O(n) es el costo de encontrar mediana / QuickSort promedio)

    Solución por Teorema Maestro:
      - a = 2 (subproblemas)
      - b = 2 (factor de reducción de tamaño)
      - f(n) = O(n)
      - n^(log_b a) = n^(log_2 2) = n^1 = n
      - Como f(n) = Theta(n^(log_b a)) = Theta(n), aplica el CASO 2 del Teorema Maestro:
        -> T(n) = Theta(n log n).

    Complejidad Espacial:
      - O(n) para almacenar los subarreglos y la profundidad de pila O(log n).

    :param pedidos: Lista de pedidos a particionar.
    :param umbral_k: Tamaño máximo de pedidos por cuadrante/zona (hoja de recursión).
    :param profundidad: Nivel actual en el árbol de recursión (determina eje lat/lon).
    :return: Lista de listas, donde cada lista interior es una zona con <= K pedidos.
    """
    n = len(pedidos)
    if n <= umbral_k:
        return [pedidos] if pedidos else []

    # Alternar eje según la profundidad de la recursión (estilo 2D K-D Tree manual)
    if profundidad % 2 == 0:
        # Eje de Latitud (Norte - Sur)
        pedidos_ordenados = quick_sort(pedidos, key=lambda p: p.lat)
    else:
        # Eje de Longitud (Este - Oeste)
        pedidos_ordenados = quick_sort(pedidos, key=lambda p: p.lon)

    medio = n // 2
    sub_izq = pedidos_ordenados[:medio]
    sub_der = pedidos_ordenados[medio:]

    # Llamadas recursivas (Vencer)
    zonas_izq = particionar_pedidos_dyv(sub_izq, umbral_k, profundidad + 1)
    zonas_der = particionar_pedidos_dyv(sub_der, umbral_k, profundidad + 1)

    # Combinar
    return zonas_izq + zonas_der


def resolver_rutas_dyv(
    nodo_inicio_id: str,
    pedidos: List[Pedido],
    grafo: Grafo,
    umbral_k: int = 5,
) -> Tuple[List[ZonaReparto], Ruta]:
    """
    Aplica Divide y Vencerás completo:
    1. Segmenta la ciudad en zonas con <= K pedidos.
    2. Resuelve cada zona localmente (mediante Greedy sobre el clúster).
    3. Conecta las zonas ordenando los clústeres por proximidad de centroides.

    Complejidad Temporal Total:
      - Partición: O(n log n)
      - Resolución local de M zonas de tamaño k <= K: M * O(k^2) <= (n/k)*O(k^2) = O(n * k).
        Como k <= K constante (e.g. 5), O(n * k) = O(n).
      - Conexión de zonas: O(M^2) donde M = n/K.
      - Total: O(n log n).
    """
    t_inicio = time.perf_counter()

    grupos_pedidos = particionar_pedidos_dyv(pedidos, umbral_k=umbral_k)
    zonas: List[ZonaReparto] = []

    for idx, grupo in enumerate(grupos_pedidos):
        coords = [(p.lat, p.lon) for p in grupo]
        c = centroide(coords)
        zona = ZonaReparto(id_zona=idx + 1, pedidos=grupo, centroide=c)
        zonas.append(zona)

    # Ordenar las zonas por distancia de su centroide al punto de partida o nodo actual
    nodo_actual_lat = grafo.nodos[nodo_inicio_id].lat
    nodo_actual_lon = grafo.nodos[nodo_inicio_id].lon

    zonas_pendientes = list(zonas)
    zonas_ordenadas: List[ZonaReparto] = []

    pos_c_lat = nodo_actual_lat
    pos_c_lon = nodo_actual_lon

    while zonas_pendientes:
        mejor_dist = float("inf")
        mejor_idx = -1
        for idx, z in enumerate(zonas_pendientes):
            d = distancia_haversine(pos_c_lat, pos_c_lon, z.centroide[0], z.centroide[1])
            if d < mejor_dist:
                mejor_dist = d
                mejor_idx = idx

        siguiente_zona = zonas_pendientes.pop(mejor_idx)
        zonas_ordenadas.append(siguiente_zona)
        pos_c_lat = siguiente_zona.centroide[0]
        pos_c_lon = siguiente_zona.centroide[1]

    # Resolver sub-ruta dentro de cada zona y concatenar
    secuencia_global = [nodo_inicio_id]
    pedidos_global = []
    distancia_total = 0.0
    nodo_cursor = nodo_inicio_id

    for zona in zonas_ordenadas:
        sub_ruta = vecino_mas_cercano(nodo_cursor, zona.pedidos, grafo, retornar_al_inicio=False)
        zona.ruta_local = sub_ruta

        # Concatenar secuencia (omitiendo duplicar el nodo de enganche si ya está)
        for nid in sub_ruta.secuencia_nodos:
            if not secuencia_global or nid != secuencia_global[-1]:
                secuencia_global.append(nid)

        pedidos_global.extend(sub_ruta.pedidos_cubiertos)
        distancia_total += sub_ruta.distancia_total_m

        if sub_ruta.secuencia_nodos:
            nodo_cursor = sub_ruta.secuencia_nodos[-1]

    t_fin = time.perf_counter()
    tiempo_ms = (t_fin - t_inicio) * 1000.0

    ruta_combinada = Ruta(
        secuencia_nodos=secuencia_global,
        pedidos_cubiertos=pedidos_global,
        distancia_total_m=round(distancia_total, 2),
        algoritmo_utilizado="Divide y Vencerás (Partición 2D + Ensamble)",
        tiempo_computo_ms=round(tiempo_ms, 3),
    )

    return zonas_ordenadas, ruta_combinada
