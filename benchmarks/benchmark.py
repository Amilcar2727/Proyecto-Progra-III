"""
Módulo de Benchmarks y Evaluación Empírica de Rendimiento.
Mide tiempos de ejecución y calidad de soluciones reales para:
- Merge Sort vs Quick Sort
- Greedy vs Held-Karp (TSP)
- Backtracking con y sin Poda (Branch & Bound)
- Mochila 0/1: PD exacta vs heurística voraz por densidad
- Divide y Vencerás vs Greedy global al crecer n

Genera datos empíricos reales para el informe técnico y la pestaña de comparación.
"""

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Asegurar que el directorio raíz del proyecto esté en sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.gestor_datos import cargar_grafo, cargar_pedidos
from core.estructuras import merge_sort, quick_sort
import random
from core.greedy import vecino_mas_cercano, mochila_voraz_por_densidad
from core.divide_venceras import resolver_rutas_dyv, resolver_por_repartidores
from core.gestor_datos import cargar_repartidores
from core.modelos import Pedido
from core.prog_dinamica import held_karp_tsp, resolver_mochila_01
from core.backtracking import buscar_rutas_backtracking
from core.grafo import matriz_para_nodos


def ejecutar_benchmarks_ordenacion(tamanios: List[int] = [10, 20, 30]) -> Dict[str, Any]:
    """Compara Merge Sort vs Quick Sort con diferentes tamaños de pedidos."""
    pedidos_base = cargar_pedidos()
    resultados = {"n": [], "merge_sort_ms": [], "quick_sort_ms": []}

    for n in tamanios:
        muestra = pedidos_base[:min(n, len(pedidos_base))]
        resultados["n"].append(len(muestra))

        # Merge Sort
        t0 = time.perf_counter()
        for _ in range(20):
            _ = merge_sort(muestra, key=lambda p: p.valor_soles)
        t_merge = ((time.perf_counter() - t0) / 20.0) * 1000.0
        resultados["merge_sort_ms"].append(round(t_merge, 4))

        # Quick Sort
        t0 = time.perf_counter()
        for _ in range(20):
            _ = quick_sort(muestra, key=lambda p: p.valor_soles)
        t_quick = ((time.perf_counter() - t0) / 20.0) * 1000.0
        resultados["quick_sort_ms"].append(round(t_quick, 4))

    return resultados


def ejecutar_benchmarks_tsp(valores_n: List[int] = [3, 5, 8, 10, 12]) -> Dict[str, Any]:
    """
    Compara empíricamente Greedy (O(n²)) contra Held-Karp (O(n² 2ⁿ)).
    Mide tiempo de cómputo y calidad de solución (distancia total en metros).
    """
    grafo = cargar_grafo()
    pedidos_base = cargar_pedidos()

    resultados = {
        "n": [],
        "tiempo_greedy_ms": [],
        "tiempo_held_karp_ms": [],
        "distancia_greedy_m": [],
        "distancia_held_karp_m": [],
        "gap_porcentaje": [],
        "speedup_greedy": [],
    }

    for n in valores_n:
        sub_pedidos = pedidos_base[:n]
        matriz = matriz_para_nodos(grafo, [p.nodo_id for p in sub_pedidos])
        origen_id = sub_pedidos[0].nodo_id

        # 1. Held-Karp (Óptimo)
        idx_hk, dist_hk, t_hk = held_karp_tsp(matriz, retornar_al_inicio=True)

        # 2. Greedy (Heurística Voraz)
        ruta_gr = vecino_mas_cercano(
            nodo_inicio_id=origen_id,
            pedidos=sub_pedidos[1:],
            grafo=grafo,
            retornar_al_inicio=True,
        )

        dist_gr = ruta_gr.distancia_total_m
        t_gr = ruta_gr.tiempo_computo_ms

        gap = ((dist_gr - dist_hk) / dist_hk * 100.0) if dist_hk > 0 else 0.0
        speedup = (t_hk / max(t_gr, 0.001))

        resultados["n"].append(n)
        resultados["tiempo_greedy_ms"].append(round(t_gr, 3))
        resultados["tiempo_held_karp_ms"].append(round(t_hk, 3))
        resultados["distancia_greedy_m"].append(round(dist_gr, 2))
        resultados["distancia_held_karp_m"].append(round(dist_hk, 2))
        resultados["gap_porcentaje"].append(round(gap, 2))
        resultados["speedup_greedy"].append(round(speedup, 1))

    return resultados


def ejecutar_benchmarks_backtracking() -> Dict[str, Any]:
    """Mide el rendimiento del Backtracking con poda en el grafo de Cusco."""
    grafo = cargar_grafo()
    pares_prueba = [
        ("N01", "N04", "Plaza de Armas -> San Pedro (Cercano)"),
        ("N02", "N11", "San Blas -> Wanchaq (Medio)"),
        ("N01", "N15", "Plaza de Armas -> UNSAAC (Largo)"),
        ("N05", "N19", "Santiago -> San Sebastián (Extremo)"),
    ]

    resultados = []
    for u, v, desc in pares_prueba:
        res = buscar_rutas_backtracking(grafo, u, v, usar_poda=True)
        completo = buscar_rutas_backtracking(grafo, u, v, usar_poda=False)
        opt_dist = res.ruta_optima[1] if res.ruta_optima else 0.0
        opt_pasos = len(res.ruta_optima[0]) if res.ruta_optima else 0
        resultados.append(
            {
                "par": f"{u} -> {v}",
                "descripcion": desc,
                "rutas_encontradas": len(res.rutas_encontradas),
                "rutas_totales_sin_poda": len(completo.rutas_encontradas),
                "ramas_podadas": res.total_ramas_podadas,
                "estados_visitados": res.total_estados_visitados,
                "estados_visitados_sin_poda": completo.total_estados_visitados,
                "distancia_optima_m": opt_dist,
                "misma_optima_sin_poda": completo.ruta_optima == res.ruta_optima,
                "nodos_camino": opt_pasos,
                "tiempo_ms": res.tiempo_computo_ms,
                "tiempo_sin_poda_ms": completo.tiempo_computo_ms,
            }
        )
    return {"casos_backtracking": resultados}


def ejecutar_benchmarks_mochila(
    valores_n: List[int] = [5, 10, 15, 20, 25, 30], capacidad_kg: float = 25.0
) -> Dict[str, Any]:
    """Mochila 0/1 por PD (óptima) frente a la heurística voraz por densidad valor/peso."""
    pedidos_base = cargar_pedidos()
    res = {"n": [], "capacidad_kg": capacidad_kg, "valor_pd": [], "valor_voraz": [],
           "tiempo_pd_ms": [], "tiempo_voraz_ms": [], "celdas_tabla": []}
    for n in valores_n:
        muestra = pedidos_base[:n]
        t0 = time.perf_counter()
        valor_pd, _, dp = resolver_mochila_01(muestra, capacidad_kg)
        t1 = time.perf_counter()
        valor_vz, _ = mochila_voraz_por_densidad(muestra, capacidad_kg)
        t2 = time.perf_counter()
        res["n"].append(n)
        res["valor_pd"].append(round(valor_pd, 2))
        res["valor_voraz"].append(round(valor_vz, 2))
        res["tiempo_pd_ms"].append(round((t1 - t0) * 1000.0, 3))
        res["tiempo_voraz_ms"].append(round((t2 - t1) * 1000.0, 3))
        res["celdas_tabla"].append(len(dp) * len(dp[0]))
    return res


def ejecutar_benchmarks_dyv(valores_n: List[int] = [30, 60, 120, 240, 480]) -> Dict[str, Any]:
    """
    Divide y Vencerás (K = 5) frente a Greedy global sobre pedidos sintéticos
    (semilla fija) repartidos en los 20 lugares de interés.
    """
    grafo = cargar_grafo()
    nodos = list(grafo.nodos.values())
    generador = random.Random(2026)
    res = {"n": [], "tiempo_dyv_ms": [], "tiempo_greedy_ms": [],
           "distancia_dyv_m": [], "distancia_greedy_m": []}
    for n in valores_n:
        pedidos = []
        for i in range(n):
            nodo = generador.choice(nodos)
            pedidos.append(Pedido(
                f"SIM-{i:04d}", "Sintético", nodo.id,
                nodo.lat + generador.uniform(-0.001, 0.001),
                nodo.lon + generador.uniform(-0.001, 0.001),
                nodo.sector, 2, 1.0, 1.0, 10.0,
            ))
        t0 = time.perf_counter()
        _, ruta_dyv = resolver_rutas_dyv("N01", pedidos, grafo, umbral_k=5)
        t1 = time.perf_counter()
        ruta_gr = vecino_mas_cercano("N01", pedidos, grafo)
        t2 = time.perf_counter()
        res["n"].append(n)
        res["tiempo_dyv_ms"].append(round((t1 - t0) * 1000.0, 3))
        res["tiempo_greedy_ms"].append(round((t2 - t1) * 1000.0, 3))
        res["distancia_dyv_m"].append(ruta_dyv.distancia_total_m)
        res["distancia_greedy_m"].append(ruta_gr.distancia_total_m)
    return res


def ejecutar_benchmark_zonas_repartidores() -> Dict[str, Any]:
    """
    Caso de uso del enunciado: los 30 pedidos reales se dividen en una zona por
    repartidor (D&C) y cada uno resuelve su zona con Held-Karp. Se compara la ruta más
    larga del equipo (lo que tarda en terminar el reparto) contra un solo repartidor
    que hace todo con Greedy desde la Plaza de Armas.
    """
    grafo = cargar_grafo()
    pedidos = cargar_pedidos()
    repartidores = cargar_repartidores()
    t0 = time.perf_counter()
    zonas = resolver_por_repartidores(pedidos, repartidores, grafo)
    t1 = time.perf_counter()
    solo = vecino_mas_cercano("N01", pedidos, grafo)
    detalle = [
        {
            "zona": z.id_zona,
            "repartidor": z.repartidor_id,
            "pedidos": len(z.pedidos),
            "distancia_m": z.ruta_local.distancia_total_m,
        }
        for z in zonas
    ]
    return {
        "zonas": detalle,
        "ruta_mas_larga_m": max(d["distancia_m"] for d in detalle),
        "distancia_total_equipo_m": round(sum(d["distancia_m"] for d in detalle), 2),
        "un_repartidor_greedy_m": solo.distancia_total_m,
        "tiempo_ms": round((t1 - t0) * 1000.0, 3),
    }


def ejecutar_todo_y_guardar(
    ruta_salida: Path = Path(__file__).resolve().parent / "resultados_benchmark.json",
) -> Dict[str, Any]:
    """Ejecuta todos los benchmarks y guarda el JSON con datos reales."""
    print("Iniciando benchmarks reales del sistema...")
    bench_sort = ejecutar_benchmarks_ordenacion()
    print("  -> Benchmarks de ordenación completados.")
    bench_tsp = ejecutar_benchmarks_tsp()
    print("  -> Benchmarks de TSP (Held-Karp vs Greedy) completados.")
    bench_bt = ejecutar_benchmarks_backtracking()
    print("  -> Benchmarks de Backtracking completados.")
    bench_mochila = ejecutar_benchmarks_mochila()
    print("  -> Benchmarks de Mochila (PD vs Voraz) completados.")
    bench_dyv = ejecutar_benchmarks_dyv()
    bench_zonas = ejecutar_benchmark_zonas_repartidores()
    print("  -> Benchmarks de Divide y Vencerás completados.")

    consolidado = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "ordenacion": bench_sort,
        "tsp_comparativa": bench_tsp,
        "backtracking": bench_bt,
        "mochila": bench_mochila,
        "divide_venceras": bench_dyv,
        "zonas_repartidores": bench_zonas,
    }

    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(consolidado, f, indent=2, ensure_ascii=False)

    print(f"Resultados exportados exitosamente a: {ruta_salida}")
    return consolidado


if __name__ == "__main__":
    ejecutar_todo_y_guardar()
