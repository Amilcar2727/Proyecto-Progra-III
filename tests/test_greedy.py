"""
Pruebas Unitarias para el Paradigma Voraz (Greedy).
Verifica la heurística de Vecino Más Cercano y Asignación de Emergencia.
"""

import pytest
from core.modelos import Grafo, Nodo, Pedido, Repartidor
from core.greedy import vecino_mas_cercano, asignar_pedido_emergencia


@pytest.fixture
def grafo_simple():
    g = Grafo()
    # Las longitudes de red, no la posición geográfica, determinan la ruta.
    g.agregar_nodo(Nodo("N01", "Origen", -13.5160, -71.9780, "Centro"))
    g.agregar_nodo(Nodo("N02", "Punto Medio", -13.5180, -71.9780, "Centro"))
    g.agregar_nodo(Nodo("N03", "Punto Lejano", -13.5220, -71.9780, "Centro"))
    g.agregar_arista("N01", "N02", 100.0)
    g.agregar_arista("N02", "N03", 200.0)
    return g


def test_vecino_cercano_orden_esperado(grafo_simple):
    pedidos = [
        Pedido("P3", "Lejano", "N03", -13.5220, -71.9780, "Centro", 2, 2.0, 3.0, 50.0),
        Pedido("P2", "Medio", "N02", -13.5180, -71.9780, "Centro", 2, 2.0, 3.0, 50.0),
    ]

    ruta = vecino_mas_cercano("N01", pedidos, grafo_simple, retornar_al_inicio=False)
    # Desde N01, N02 está más cerca que N03, por lo que el orden debe ser N01 -> N02 -> N03
    assert ruta.secuencia_nodos == ["N01", "N02", "N03"]
    assert ruta.pedidos_cubiertos == ["P2", "P3"]
    assert ruta.distancia_total_m == 300.0


def test_vecino_cercano_con_retorno(grafo_simple):
    pedidos = [
        Pedido("P2", "Medio", "N02", -13.5180, -71.9780, "Centro", 2, 2.0, 3.0, 50.0),
    ]
    ruta = vecino_mas_cercano("N01", pedidos, grafo_simple, retornar_al_inicio=True)
    assert ruta.secuencia_nodos == ["N01", "N02", "N01"]
    assert ruta.distancia_total_m == 200.0


def test_vecino_cercano_respeta_distancias_asimetricas():
    grafo = Grafo()
    for nodo_id in ("A", "B", "C"):
        grafo.agregar_nodo(Nodo(nodo_id, nodo_id, 0.0, 0.0, "test"))
    grafo.agregar_arista("A", "B", 50.0, bidireccional=False)
    grafo.agregar_arista("A", "C", 10.0, bidireccional=False)
    grafo.agregar_arista("C", "B", 5.0, bidireccional=False)
    grafo.agregar_arista("B", "C", 100.0, bidireccional=False)
    pedidos = [
        Pedido("PB", "B", "B", 0, 0, "test", 2, 1.0, 1.0, 10.0),
        Pedido("PC", "C", "C", 0, 0, "test", 2, 1.0, 1.0, 10.0),
    ]

    ruta = vecino_mas_cercano("A", pedidos, grafo)

    assert ruta.secuencia_nodos == ["A", "C", "B"]
    assert ruta.distancia_total_m == 15.0


def test_asignacion_emergencia_mas_cercano(grafo_simple):
    rep_cercano = Repartidor("R1", "Repartidor 1", "Moto", "N02", 20.0, 30.0)
    rep_lejano = Repartidor("R2", "Repartidor 2", "Furgón", "N03", 50.0, 80.0)

    # Pedido en N01 (más cerca de N02 que de N03)
    urgente = Pedido("PU", "Emergencia", "N01", -13.5160, -71.9780, "Centro", 1, 3.0, 5.0, 100.0)

    asignado, dist, _ = asignar_pedido_emergencia(urgente, [rep_cercano, rep_lejano], grafo_simple)
    assert asignado is not None
    assert asignado.id == "R1"


def test_asignacion_emergencia_filtro_por_capacidad(grafo_simple):
    # Repartidor cercano no tiene suficiente capacidad de peso (1 kg < 5 kg)
    rep_debil = Repartidor("R1", "Bici Ligera", "Bici", "N02", 1.0, 5.0)
    rep_capaz = Repartidor("R2", "Furgón", "Furgón", "N03", 50.0, 80.0)

    urgente = Pedido("PU", "Carga Pesada", "N01", -13.5160, -71.9780, "Centro", 1, 5.0, 5.0, 100.0)

    asignado, _, _ = asignar_pedido_emergencia(urgente, [rep_debil, rep_capaz], grafo_simple)
    assert asignado is not None
    assert asignado.id == "R2"
