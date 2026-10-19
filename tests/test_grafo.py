"""Pruebas de caminos mínimos y cache de red vial."""

import math

import pytest

from core.geo import distancia_haversine, nodo_mas_cercano_haversine
from core.gestor_datos import cargar_grafo
from core.grafo import (
    calcular_matriz_distancias,
    dijkstra,
    obtener_camino_mas_corto,
    obtener_matriz_distancias,
    reconstruir_camino,
    geometria_de_ruta,
)
from core.modelos import Grafo, Nodo


def _grafo_con_nodos(ids):
    grafo = Grafo()
    for nodo_id in ids:
        grafo.agregar_nodo(Nodo(nodo_id, nodo_id, 0.0, 0.0, "test"))
    return grafo


def test_dijkstra_reconstruye_optimo_en_grafo_pequeno():
    grafo = _grafo_con_nodos(["A", "B", "C", "D"])
    grafo.agregar_arista("A", "B", 2.0, bidireccional=False)
    grafo.agregar_arista("A", "C", 10.0, bidireccional=False)
    grafo.agregar_arista("B", "C", 3.0, bidireccional=False)
    grafo.agregar_arista("C", "D", 4.0, bidireccional=False)
    grafo.agregar_arista("B", "D", 10.0, bidireccional=False)

    distancias, predecesores = dijkstra(grafo, "A")

    assert distancias["D"] == 9.0
    assert reconstruir_camino(predecesores, "A", "D") == ["A", "B", "C", "D"]
    assert reconstruir_camino(predecesores, "A", "A") == ["A"]


def test_geometria_de_ruta_concatena_curvas_en_sentido_correcto():
    grafo = _grafo_con_nodos(["A", "B", "C"])
    grafo.agregar_arista(
        "A",
        "B",
        10.0,
        bidireccional=False,
        geometria=[(0.0, 0.0), (0.0, 0.5), (1.0, 1.0)],
    )
    grafo.agregar_arista(
        "B",
        "C",
        12.0,
        bidireccional=False,
        geometria=[(1.0, 1.0), (1.5, 1.5), (2.0, 2.0)],
    )

    assert geometria_de_ruta(grafo, ["A", "C"]) == [
        (0.0, 0.0),
        (0.0, 0.5),
        (1.0, 1.0),
        (1.5, 1.5),
        (2.0, 2.0),
    ]


def test_asignacion_de_coordenada_elige_nodo_mas_cercano_por_haversine():
    nodos = [
        Nodo("A", "A", 0.0, 0.0, "test"),
        Nodo("B", "B", 0.0, 1.0, "test"),
    ]
    nodo_id, distancia = nodo_mas_cercano_haversine(0.0, 0.2, nodos)
    assert nodo_id == "A"
    assert distancia == distancia_haversine(0.0, 0.0, 0.0, 0.2)


def test_cierre_actualiza_matriz_y_puede_hacer_inalcanzable():
    grafo = _grafo_con_nodos(["S", "A", "B", "T"])
    grafo.agregar_arista("S", "A", 1.0, bidireccional=False)
    grafo.agregar_arista("A", "T", 1.0, bidireccional=False)
    grafo.agregar_arista("S", "B", 2.0, bidireccional=False)
    grafo.agregar_arista("B", "T", 2.0, bidireccional=False)

    matriz, _ = calcular_matriz_distancias(grafo)
    assert matriz["S"]["T"] == 2.0
    assert obtener_camino_mas_corto(grafo, "S", "T") == ["S", "A", "T"]

    grafo.cambiar_estado_calle("S", "A", activa=False)
    assert grafo.matriz_distancias is None
    assert obtener_matriz_distancias(grafo)["S"]["T"] == 4.0
    assert obtener_camino_mas_corto(grafo, "S", "T") == ["S", "B", "T"]

    grafo.cambiar_estado_calle("S", "B", activa=False)
    assert math.isinf(obtener_matriz_distancias(grafo)["S"]["T"])
    assert obtener_camino_mas_corto(grafo, "S", "T") == []


def test_cierre_bidireccional_cierra_arcos_en_ambos_sentidos():
    grafo = _grafo_con_nodos(["A", "B"])
    grafo.agregar_arista("A", "B", 12.0, bidireccional=True)
    grafo.cambiar_estado_calle("A", "B", activa=False)

    matriz = obtener_matriz_distancias(grafo)
    assert math.isinf(matriz["A"]["B"])
    assert math.isinf(matriz["B"]["A"])


@pytest.fixture(scope="module")
def grafo_cache():
    return cargar_grafo()


def test_cache_es_fuertemente_conexo_y_cumple_desigualdad_triangular(grafo_cache):
    matriz = obtener_matriz_distancias(grafo_cache)
    for origen in grafo_cache.nodos:
        assert all(math.isfinite(matriz[origen][destino]) for destino in grafo_cache.nodos)
    for a in grafo_cache.nodos:
        for b in grafo_cache.nodos:
            for c in grafo_cache.nodos:
                assert matriz[a][c] <= matriz[a][b] + matriz[b][c] + 1e-9


def test_cache_aristas_tienen_peso_mayor_que_recta_y_geometria_con_extremos(grafo_cache):
    for arista in grafo_cache.todas_las_aristas():
        origen = grafo_cache.nodos[arista.origen_id]
        destino = grafo_cache.nodos[arista.destino_id]
        directa = distancia_haversine(origen.lat, origen.lon, destino.lat, destino.lon)
        assert arista.longitud_m >= directa * 0.98
        assert len(arista.geometria) >= 2
        assert arista.geometria[0] == pytest.approx((origen.lat, origen.lon), abs=1e-7)
        assert arista.geometria[-1] == pytest.approx((destino.lat, destino.lon), abs=1e-7)
