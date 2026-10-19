"""
Módulo de Programación Dinámica (PD).
Implementaciones manuales de:
1. Mochila 0/1 (Knapsack) con matriz completa (N+1) x (W+1) y reconstrucción.
2. Held-Karp (TSP Óptimo con Bitmask y Memoización).

Prohibido el uso de librerías externas de optimización o itertools.
"""

import time
import math
from typing import List, Optional, Tuple
from core.grafo import validar_distancias
from core.modelos import Pedido, Ruta


def discretizar_peso(peso_kg: float, escala: int) -> int:
    """
    Convierte un peso en kg a unidades enteras de 1/escala kg, redondeando HACIA ARRIBA.

    Redondear hacia arriba garantiza que la solución nunca exceda la capacidad real:
    un pedido de 2.25 kg con escala 10 ocupa 23 unidades (2.3 kg), nunca 22.
    El round(..., 6) previo elimina el error de punto flotante (2.2 * 10 = 22.000000000000004).
    """
    return math.ceil(round(peso_kg * escala, 6))


def resolver_mochila_01(
    pedidos: List[Pedido],
    capacidad_peso_kg: float,
    escala: int = 10,
) -> Tuple[float, List[Pedido], List[List[float]]]:
    """
    Resuelve el problema de la Mochila 0/1 para maximizar el valor de pedidos sin exceder peso.

    Paradigma: Programación Dinámica (PD).
    Principio: Subestructura Óptima y Subproblemas Solapados (Principio de Optimalidad de Bellman).

    Discretización: la tabla se indexa por enteros, así que los pesos se expresan en
    unidades de 1/escala kg (escala = 10 -> precisión de 0.1 kg). Los pesos se redondean
    hacia arriba y la capacidad hacia abajo, por lo que la carga elegida nunca supera la
    capacidad real. (La versión anterior redondeaba al kg más cercano y podía exceder
    la capacidad: p. ej. 5.2 kg con capacidad 5 kg.)

    Ecuación de Recurrencia (w en unidades de 1/escala kg):
      DP[i][w] = valor máximo usando un subconjunto de los primeros i pedidos con peso <= w.
      - Caso Base:
          DP[0][w] = 0   para todo w in [0..W]
      - Paso Inductivo:
          Si peso[i] > w:
              DP[i][w] = DP[i-1][w]
          Si peso[i] <= w:
              DP[i][w] = max(DP[i-1][w], DP[i-1][w - peso[i]] + valor[i])

    Complejidad Temporal:
      - O(N · W), con W = capacidad_kg · escala (número de columnas de la tabla).
      - Es pseudo-polinomial: depende del VALOR numérico de W, no del tamaño de su
        representación. Multiplicar la precisión por 10 multiplica el tiempo por 10.

    Complejidad Espacial:
      - O(N · W) para almacenar la tabla DP bidimensional y permitir la reconstrucción.

    :param pedidos: Lista de pedidos disponibles.
    :param capacidad_peso_kg: Capacidad máxima en kg (admite decimales).
    :param escala: Unidades por kg de la tabla (10 = precisión de 0.1 kg).
    :return: Tupla con (valor_maximo, lista_pedidos_seleccionados, matriz_dp_completa).
             La matriz tiene W + 1 columnas; la columna c equivale a c / escala kg.
    """
    if escala < 1:
        raise ValueError("La escala de discretización debe ser >= 1.")
    if capacidad_peso_kg < 0:
        raise ValueError("La capacidad no puede ser negativa.")

    n = len(pedidos)
    w_max = math.floor(round(capacidad_peso_kg * escala, 6))

    # Inicializar matriz DP de tamaño (n + 1) x (w_max + 1) con ceros
    dp: List[List[float]] = [[0.0 for _ in range(w_max + 1)] for _ in range(n + 1)]

    # Pesos discretizados (redondeo hacia arriba) para indexar la matriz
    if any(p.peso_kg < 0 for p in pedidos):
        raise ValueError("Los pesos de los pedidos no pueden ser negativos.")
    pesos = [discretizar_peso(p.peso_kg, escala) for p in pedidos]
    valores = [p.valor_soles for p in pedidos]

    # Llenado de la tabla DP de abajo hacia arriba (Bottom-Up)
    for i in range(1, n + 1):
        w_i = pesos[i - 1]
        v_i = valores[i - 1]
        for w in range(w_max + 1):
            if w_i > w:
                dp[i][w] = dp[i - 1][w]
            else:
                opcion_sin_tomar = dp[i - 1][w]
                opcion_tomando = dp[i - 1][w - w_i] + v_i
                dp[i][w] = opcion_tomando if opcion_tomando > opcion_sin_tomar else opcion_sin_tomar

    valor_optimo = dp[n][w_max]

    # Reconstrucción de la solución (Backtracking sobre la tabla DP)
    pedidos_seleccionados: List[Pedido] = []
    w_restante = w_max
    for i in range(n, 0, -1):
        if dp[i][w_restante] != dp[i - 1][w_restante]:
            # El pedido i-1 fue incluido en la mochila
            pedido_elegido = pedidos[i - 1]
            pedidos_seleccionados.append(pedido_elegido)
            w_restante -= pesos[i - 1]

    # Invertir para que queden en orden original
    pedidos_seleccionados.reverse()

    return valor_optimo, pedidos_seleccionados, dp


def held_karp_tsp(
    matriz_distancias: List[List[float]],
    nombres: Optional[List[str]] = None,
    retornar_al_inicio: bool = True,
) -> Tuple[List[int], float, float]:
    """
    Resuelve el Problema del Viajante de Comercio (TSP) de forma EXACTA usando Held-Karp.

    Paradigma: Programación Dinámica con Bitmask (Máscara de Bits).
    Idea: El estado se codifica como (mask, u), donde mask es un entero cuyos bits
          indican el subconjunto de nodos visitados, y u es el último nodo visitado.
          Se memoizan los subproblemas para evitar recalcular permutaciones equivalentes.

    Ecuación de Recurrencia:
      C(mask, u) = costo mínimo de visitar todos los nodos restantes partiendo desde u,
                   habiendo visitado ya el conjunto codificado en mask.
      C(mask, u) = min_{v no en mask} { dist(u, v) + C(mask | (1 << v), v) }
      - Caso Base:
          Cuando mask == (1 << n) - 1 (todos visitados):
          Si retorna al inicio: dist(u, 0)
          Si no retorna: 0

    Complejidad Temporal:
      - Estados posibles: 2ⁿ · n
      - Transiciones por estado: n
      - Complejidad: O(n² · 2ⁿ). Para n = 12: 144 · 4096 ≈ 5.9 × 10⁵ operaciones (~0.1 s).
    
    Complejidad Espacial:
      - O(n · 2ⁿ) para la tabla de memoización memo[mask][u].

    :param matriz_distancias: Matriz dirigida de distancias mínimas por calles.
    :param nombres: Etiquetas opcionales de los puntos.
    :param retornar_al_inicio: Si es True, incluye el retorno al origen (TSP clásico).
    :return: Tupla con (secuencia_indices_optima, distancia_minima_m, tiempo_ms).
    """
    t_inicio = time.perf_counter()
    validar_distancias(matriz_distancias)
    n = len(matriz_distancias)

    if n == 0:
        return [], 0.0, 0.0
    if n == 1:
        return ([0, 0] if retornar_al_inicio else [0]), 0.0, 0.0

    # 2. Tabla de memoización: memo[mask][u] = (costo_minimo, mejor_siguiente_nodo)
    # mask va desde 0 hasta (1 << n) - 1
    total_estados = 1 << n
    memo: List[List[Optional[Tuple[float, int]]]] = [
        [None for _ in range(n)] for _ in range(total_estados)
    ]
    mascara_completa = (1 << n) - 1

    def _resolver_dp(mask: int, u: int) -> Tuple[float, int]:
        if mask == mascara_completa:
            costo_final = matriz_distancias[u][0] if retornar_al_inicio else 0.0
            return costo_final, -1

        if memo[mask][u] is not None:
            return memo[mask][u]

        mejor_costo = float("inf")
        mejor_sig = -1

        for v in range(n):
            # Si el bit v no está encendido en la máscara (no visitado)
            if not (mask & (1 << v)):
                nueva_mascara = mask | (1 << v)
                costo_sub, _ = _resolver_dp(nueva_mascara, v)
                costo_total = matriz_distancias[u][v] + costo_sub

                if costo_total < mejor_costo:
                    mejor_costo = costo_total
                    mejor_sig = v

        memo[mask][u] = (mejor_costo, mejor_sig)
        return memo[mask][u]

    # Iniciar desde el nodo 0 con máscara que solo contiene al nodo 0: (1 << 0) = 1
    distancia_optima, _ = _resolver_dp(1, 0)
    if not math.isfinite(distancia_optima):
        raise ValueError("No existe un recorrido TSP dirigido que visite todos los nodos.")

    # 3. Reconstruir la ruta óptima
    ruta_indices = [0]
    mask_cursor = 1
    u_cursor = 0

    while mask_cursor != mascara_completa:
        estado = memo[mask_cursor][u_cursor]
        if estado is None or estado[1] == -1:
            break
        sig = estado[1]
        ruta_indices.append(sig)
        mask_cursor |= (1 << sig)
        u_cursor = sig

    if retornar_al_inicio:
        ruta_indices.append(0)

    t_fin = time.perf_counter()
    tiempo_ms = (t_fin - t_inicio) * 1000.0

    return ruta_indices, round(distancia_optima, 2), round(tiempo_ms, 3)
