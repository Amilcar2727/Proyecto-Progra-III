"""
Módulo de Divide y Vencerás (D&C) para Segmentación Espacial de Rutas.
Implementación manual de:
1. Partición recursiva 2D por mediana alternada (Lat/Lon) hasta un umbral K de pedidos.
2. Partición recursiva en exactamente R zonas, una por repartidor.
3. Resolución local de cada zona y combinación de las sub-rutas.

Prohibido el uso de librerías externas de partición o k-d trees precompilados.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from core.geo import centroide
from core.modelos import Grafo, Pedido, Repartidor, Ruta
from core.estructuras import quick_sort
from core.greedy import vecino_mas_cercano
from core.grafo import obtener_matriz_distancias, matriz_para_nodos
from core.prog_dinamica import held_karp_tsp

# Por encima de este tamaño de zona, Held-Karp O(k² 2^k) deja de ser instantáneo.
LIMITE_ZONA_EXACTA = 10


@dataclass
class ZonaReparto:
    """Representa un clúster geográfico generado por la partición recursiva."""
    id_zona: int
    pedidos: List[Pedido]
    centroide: Tuple[float, float] = (0.0, 0.0)
    ruta_local: Optional[Ruta] = None
    repartidor_id: Optional[str] = None


def _ordenar_por_eje(pedidos: List[Pedido], profundidad: int) -> List[Pedido]:
    """Ordena por latitud en niveles pares y por longitud en niveles impares."""
    if profundidad % 2 == 0:
        return quick_sort(pedidos, key=lambda p: p.lat)   # Norte - Sur
    return quick_sort(pedidos, key=lambda p: p.lon)       # Este - Oeste


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
      T(n) = 2 T(n/2) + Θ(n log n)   (el trabajo no recursivo es ORDENAR con QuickSort)

    Solución (Teorema Maestro, forma extendida del caso 2):
      - a = 2, b = 2  ->  n^(log_b a) = n
      - f(n) = Θ(n log n) = Θ(n^(log_b a) · log^1 n)  -> k = 1
      - Caso 2 extendido: f(n) = Θ(n^(log_b a) log^k n)  =>  T(n) = Θ(n log^(k+1) n)
        -> T(n) = Θ(n log² n)  (caso promedio de QuickSort).
      Si en lugar de ordenar se usara selección de la mediana en O(n) (Quickselect),
      f(n) = Θ(n) y se obtendría Θ(n log n) por el caso 2 clásico.

    Complejidad Espacial:
      - O(n) para los subarreglos de cada nivel y O(log n) de profundidad de pila.

    :param pedidos: Lista de pedidos a particionar.
    :param umbral_k: Tamaño máximo de pedidos por zona (hoja de recursión).
    :param profundidad: Nivel actual en el árbol de recursión (determina eje lat/lon).
    :return: Lista de listas, donde cada lista interior es una zona con <= K pedidos.
    """
    if umbral_k < 1:
        raise ValueError("El umbral K debe ser al menos 1.")
    n = len(pedidos)
    if n <= umbral_k:
        return [pedidos] if pedidos else []

    pedidos_ordenados = _ordenar_por_eje(pedidos, profundidad)

    medio = n // 2
    sub_izq = pedidos_ordenados[:medio]
    sub_der = pedidos_ordenados[medio:]

    # Llamadas recursivas (Vencer)
    zonas_izq = particionar_pedidos_dyv(sub_izq, umbral_k, profundidad + 1)
    zonas_der = particionar_pedidos_dyv(sub_der, umbral_k, profundidad + 1)

    # Combinar
    return zonas_izq + zonas_der


def particionar_en_r_zonas(
    pedidos: List[Pedido],
    r: int,
    profundidad: int = 0,
) -> List[List[Pedido]]:
    """
    Divide los pedidos en EXACTAMENTE r zonas espaciales contiguas (una por repartidor).

    Paradigma: Divide y Vencerás.
    Idea: si r == 1 la zona es todo el conjunto (caso base). Si no:
          1. DIVIDIR: ordena por el eje del nivel y corta en proporción
             r_izq = floor(r/2) : r_der = ceil(r/2), de modo que cada zona final tenga
             aproximadamente n/r pedidos (por ejemplo, r = 3 corta en 1/3 y 2/3).
          2. VENCER: resuelve la mitad izquierda con r_izq zonas y la derecha con r_der.
          3. COMBINAR: concatena las listas de zonas.

    Recurrencia: T(n, r) = T(n·r_izq/r, r_izq) + T(n·r_der/r, r_der) + Θ(n log n).
    El árbol tiene profundidad ceil(log2 r) y en cada nivel se ordenan n elementos:
      T(n, r) = Θ(n log n · log r).
    Espacio: O(n).
    """
    if r < 1:
        raise ValueError("Debe haber al menos una zona.")
    if r == 1 or len(pedidos) <= 1:
        zonas = [list(pedidos)]
        # Si hay más repartidores que pedidos, las zonas sobrantes quedan vacías.
        return zonas + [[] for _ in range(r - 1)]

    r_izq = r // 2
    r_der = r - r_izq
    ordenados = _ordenar_por_eje(pedidos, profundidad)
    corte = (len(ordenados) * r_izq) // r

    return (
        particionar_en_r_zonas(ordenados[:corte], r_izq, profundidad + 1)
        + particionar_en_r_zonas(ordenados[corte:], r_der, profundidad + 1)
    )


def _distancia_a_zona(
    matriz: Dict[str, Dict[str, float]], desde: str, zona: ZonaReparto
) -> float:
    """Distancia por calles desde un nodo hasta el pedido más cercano de la zona. O(k)."""
    mejor = float("inf")
    for p in zona.pedidos:
        d = matriz[desde][p.nodo_id]
        if d < mejor:
            mejor = d
    return mejor


def resolver_rutas_dyv(
    nodo_inicio_id: str,
    pedidos: List[Pedido],
    grafo: Grafo,
    umbral_k: int = 5,
) -> Tuple[List[ZonaReparto], Ruta]:
    """
    Aplica Divide y Vencerás completo para UN repartidor:
    1. Segmenta la ciudad en M zonas con <= K pedidos (M ≈ n/K).
    2. Desde la posición actual, entra a la zona cuyo pedido más cercano esté a menor
       distancia por calles (decisión voraz entre zonas).
    3. Resuelve esa zona con Vecino Más Cercano y continúa desde su último pedido.

    Complejidad Temporal (n pedidos, M = n/K zonas, K constante):
      - Partición: Θ(n log² n) (ver particionar_pedidos_dyv).
      - Elección de la siguiente zona: en la vuelta i se revisan (M - i) zonas a O(K) cada
        una -> Σ (M - i)·K = O(M² · K) = O(n² / K).
      - Rutas locales: M zonas · O(K²) = O(n · K).
      - Total: O(n² / K). Con n pequeño domina la partición; al crecer n domina la
        elección entre zonas. Mucho menor que el TSP exacto, pero no es O(n log n).
    Complejidad Espacial: O(n) más la matriz de distancias precalculada O(V²).
    """
    t_inicio = time.perf_counter()
    if nodo_inicio_id not in grafo.nodos:
        raise ValueError(f"El nodo inicial {nodo_inicio_id!r} no existe.")

    grupos_pedidos = particionar_pedidos_dyv(pedidos, umbral_k=umbral_k)
    zonas: List[ZonaReparto] = []

    for idx, grupo in enumerate(grupos_pedidos):
        coords = [(p.lat, p.lon) for p in grupo]
        zonas.append(ZonaReparto(id_zona=idx + 1, pedidos=grupo, centroide=centroide(coords)))

    zonas_pendientes = list(zonas)
    zonas_ordenadas: List[ZonaReparto] = []
    nodo_cursor = nodo_inicio_id
    matriz = obtener_matriz_distancias(grafo)

    while zonas_pendientes:
        mejor_dist = float("inf")
        mejor_idx = -1
        for idx, z in enumerate(zonas_pendientes):
            d = _distancia_a_zona(matriz, nodo_cursor, z)
            if d < mejor_dist:
                mejor_dist = d
                mejor_idx = idx

        if mejor_idx < 0:
            raise ValueError(f"No se pudo seleccionar una zona alcanzable desde {nodo_cursor}.")
        siguiente_zona = zonas_pendientes.pop(mejor_idx)
        siguiente_zona.ruta_local = vecino_mas_cercano(
            nodo_cursor, siguiente_zona.pedidos, grafo, retornar_al_inicio=False
        )
        zonas_ordenadas.append(siguiente_zona)
        nodo_cursor = siguiente_zona.ruta_local.secuencia_nodos[-1]

    # Combinar: concatenar sub-rutas (sin duplicar el nodo de enganche).
    secuencia_global = [nodo_inicio_id]
    pedidos_global: List[str] = []
    distancia_total = 0.0

    for zona in zonas_ordenadas:
        sub_ruta = zona.ruta_local
        for nid in sub_ruta.secuencia_nodos:
            if nid != secuencia_global[-1]:
                secuencia_global.append(nid)
        pedidos_global.extend(sub_ruta.pedidos_cubiertos)
        distancia_total += sub_ruta.distancia_total_m

    tiempo_ms = (time.perf_counter() - t_inicio) * 1000.0
    ruta_combinada = Ruta(
        secuencia_nodos=secuencia_global,
        pedidos_cubiertos=pedidos_global,
        distancia_total_m=round(distancia_total, 2),
        algoritmo_utilizado="Divide y Vencerás (Partición 2D + Ensamble)",
        tiempo_computo_ms=round(tiempo_ms, 3),
    )
    return zonas_ordenadas, ruta_combinada


def ruta_optima_en_zona(
    nodo_inicio_id: str, pedidos: List[Pedido], grafo: Grafo
) -> Ruta:
    """
    Ruta de una sub-zona: exacta con Held-Karp (PD) si la zona tiene <= LIMITE_ZONA_EXACTA
    pedidos; si no, Vecino Más Cercano. Recorrido abierto (no vuelve al inicio).

    Complejidad: O(k² 2^k) con k <= 10 (exacta) u O(k²) (voraz).
    """
    t_inicio = time.perf_counter()
    if not pedidos:
        return Ruta([nodo_inicio_id], [], 0.0, "Zona vacía", 0.0)
    if len(pedidos) > LIMITE_ZONA_EXACTA:
        return vecino_mas_cercano(nodo_inicio_id, pedidos, grafo, retornar_al_inicio=False)

    nodos = [nodo_inicio_id] + [p.nodo_id for p in pedidos]
    matriz = matriz_para_nodos(grafo, nodos)
    indices, distancia, _ = held_karp_tsp(matriz, retornar_al_inicio=False)
    orden = [pedidos[i - 1] for i in indices[1:]]
    return Ruta(
        secuencia_nodos=[nodo_inicio_id] + [p.nodo_id for p in orden],
        pedidos_cubiertos=[p.id for p in orden],
        distancia_total_m=round(distancia, 2),
        algoritmo_utilizado="Held-Karp por zona",
        tiempo_computo_ms=round((time.perf_counter() - t_inicio) * 1000.0, 3),
    )


def resolver_por_repartidores(
    pedidos: List[Pedido],
    repartidores: List[Repartidor],
    grafo: Grafo,
) -> List[ZonaReparto]:
    """
    Caso de uso del enunciado: dividir la ciudad para que CADA repartidor resuelva
    solo la ruta óptima de su sub-zona.

    1. DIVIDIR: particionar_en_r_zonas crea R zonas espaciales balanceadas (R repartidores).
    2. ASIGNAR: emparejamiento voraz zona-repartidor. Se evalúan los R² pares
       (repartidor, zona) por distancia desde la base del repartidor hasta el pedido más
       cercano de la zona; se ordenan con QuickSort y se toma el menor par cuyos dos
       extremos sigan libres.
    3. VENCER: cada repartidor calcula la ruta de su zona (Held-Karp si k <= 10).

    Complejidad: partición Θ(n log n log R) + emparejamiento O(R² log R + R·n)
                 + rutas Σ O(k² 2^k) con k ≈ n/R.
    No verifica capacidad de carga: eso lo resuelve la Mochila (PD) por repartidor.
    """
    if not repartidores:
        raise ValueError("Se necesita al menos un repartidor.")
    r = len(repartidores)
    matriz = obtener_matriz_distancias(grafo)

    grupos = particionar_en_r_zonas(pedidos, r)
    zonas = [
        ZonaReparto(
            id_zona=i + 1,
            pedidos=g,
            centroide=centroide([(p.lat, p.lon) for p in g]),
        )
        for i, g in enumerate(grupos)
    ]

    pares = []
    for rep in repartidores:
        base = rep.nodo_actual_id or rep.nodo_inicio_id
        for z in zonas:
            d = _distancia_a_zona(matriz, base, z) if z.pedidos else 0.0
            pares.append((d, rep, z))
    pares = quick_sort(pares, key=lambda t: t[0])

    asignados_rep = set()
    asignadas_zona = set()
    for d, rep, z in pares:
        if rep.id in asignados_rep or z.id_zona in asignadas_zona:
            continue
        z.repartidor_id = rep.id
        base = rep.nodo_actual_id or rep.nodo_inicio_id
        z.ruta_local = ruta_optima_en_zona(base, z.pedidos, grafo)
        asignados_rep.add(rep.id)
        asignadas_zona.add(z.id_zona)

    return zonas
