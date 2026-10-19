"""
Pruebas Unitarias para Divide y Vencerás (D&C).
Verifica la partición recursiva espacial, conservación de pedidos y resolución local.
"""

import pytest
from core.modelos import Grafo, Nodo, Pedido
from core.divide_venceras import particionar_pedidos_dyv, resolver_rutas_dyv


@pytest.fixture
def pedidos_dispersos():
    return [
        Pedido("P1", "C1", "N01", -13.510, -71.980, "Norte", 1, 2.0, 3.0, 50.0),
        Pedido("P2", "C2", "N01", -13.512, -71.979, "Norte", 2, 2.0, 3.0, 50.0),
        Pedido("P3", "C3", "N02", -13.520, -71.970, "Sur", 1, 3.0, 4.0, 80.0),
        Pedido("P4", "C4", "N02", -13.522, -71.969, "Sur", 3, 1.0, 2.0, 30.0),
        Pedido("P5", "C5", "N03", -13.530, -71.950, "Este", 2, 4.0, 5.0, 110.0),
        Pedido("P6", "C6", "N03", -13.532, -71.948, "Este", 1, 2.5, 3.5, 75.0),
    ]


@pytest.fixture
def grafo_minimo():
    g = Grafo()
    g.agregar_nodo(Nodo("N01", "Nodo 1", -13.510, -71.980, "Norte"))
    g.agregar_nodo(Nodo("N02", "Nodo 2", -13.520, -71.970, "Sur"))
    g.agregar_nodo(Nodo("N03", "Nodo 3", -13.530, -71.950, "Este"))
    g.agregar_arista("N01", "N02", 100.0)
    g.agregar_arista("N02", "N03", 200.0)
    return g


def test_particion_tamanios_menores_o_iguales_a_k(pedidos_dispersos):
    k = 2
    zonas = particionar_pedidos_dyv(pedidos_dispersos, umbral_k=k)
    # Ninguna zona debe exceder K
    for z in zonas:
        assert len(z) <= k

    # Conservación de todos los pedidos
    todos_los_ids = [p.id for z in zonas for p in z]
    assert len(todos_los_ids) == len(pedidos_dispersos)
    assert set(todos_los_ids) == {p.id for p in pedidos_dispersos}


def test_resolver_rutas_dyv_ensamble(pedidos_dispersos, grafo_minimo):
    zonas, ruta_global = resolver_rutas_dyv(
        nodo_inicio_id="N01",
        pedidos=pedidos_dispersos,
        grafo=grafo_minimo,
        umbral_k=2,
    )
    assert len(zonas) >= 3
    assert len(ruta_global.pedidos_cubiertos) == len(pedidos_dispersos)
    assert ruta_global.distancia_total_m > 0.0
    assert ruta_global.secuencia_nodos[0] == "N01"


def test_particion_en_r_zonas_exactas(pedidos_dispersos):
    from core.divide_venceras import particionar_en_r_zonas
    for r in (1, 2, 3, 4):
        zonas = particionar_en_r_zonas(pedidos_dispersos, r)
        assert len(zonas) == r
        ids = [p.id for z in zonas for p in z]
        assert sorted(ids) == sorted(p.id for p in pedidos_dispersos)
        # Zonas balanceadas: tamaños difieren a lo sumo en 1 (6 pedidos / r)
        tamanios = [len(z) for z in zonas]
        assert max(tamanios) - min(tamanios) <= 1


def test_un_repartidor_por_zona():
    from core.divide_venceras import resolver_por_repartidores
    from core.gestor_datos import cargar_grafo, cargar_pedidos, cargar_repartidores
    grafo = cargar_grafo()
    pedidos = cargar_pedidos()
    repartidores = cargar_repartidores()
    zonas = resolver_por_repartidores(pedidos, repartidores, grafo)
    assert len(zonas) == len(repartidores)
    assert {z.repartidor_id for z in zonas} == {r.id for r in repartidores}
    cubiertos = [pid for z in zonas for pid in z.ruta_local.pedidos_cubiertos]
    assert sorted(cubiertos) == sorted(p.id for p in pedidos)


def test_held_karp_por_zona_no_peor_que_greedy():
    from core.divide_venceras import ruta_optima_en_zona
    from core.greedy import vecino_mas_cercano
    from core.gestor_datos import cargar_grafo, cargar_pedidos
    grafo = cargar_grafo()
    pedidos = cargar_pedidos()[:8]
    exacta = ruta_optima_en_zona("N01", pedidos, grafo)
    voraz = vecino_mas_cercano("N01", pedidos, grafo)
    assert exacta.distancia_total_m <= voraz.distancia_total_m + 1e-6
    assert sorted(exacta.pedidos_cubiertos) == sorted(p.id for p in pedidos)
