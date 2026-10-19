"""
Pruebas Unitarias para Programación Dinámica (PD).
Verifica Mochila 0/1 con casos de libro de texto y Held-Karp TSP con óptimo determinista.
"""

import pytest
from core.modelos import Pedido
from core.prog_dinamica import resolver_mochila_01, held_karp_tsp


def test_mochila_caso_clasico_libro():
    """
    Caso clásico de libro:
    Item 1: peso 1, valor 15
    Item 2: peso 2, valor 10
    Item 3: peso 3, valor 30
    Capacidad W = 4.
    Solución óptima: Tomar Item 1 + Item 3 -> Peso = 4, Valor = 45.
    (La heurística voraz por densidad valor/peso tomaría Item 1 + Item 2 = 25, siendo subóptima).
    """
    pedidos = [
        Pedido("P1", "Item 1", "N01", 0, 0, "S1", 1, 1.0, 1.0, 15.0),
        Pedido("P2", "Item 2", "N02", 0, 0, "S1", 1, 2.0, 1.0, 10.0),
        Pedido("P3", "Item 3", "N03", 0, 0, "S1", 1, 3.0, 1.0, 30.0),
    ]

    valor_max, seleccionados, dp = resolver_mochila_01(pedidos, capacidad_peso_kg=4)

    assert valor_max == 45.0
    ids_elegidos = [p.id for p in seleccionados]
    assert ids_elegidos == ["P1", "P3"]
    assert sum(p.peso_kg for p in seleccionados) <= 4.0


def test_mochila_capacidad_cero_o_vacio():
    pedidos = [
        Pedido("P1", "Item 1", "N01", 0, 0, "S1", 1, 2.0, 1.0, 20.0),
    ]
    val, sel, _ = resolver_mochila_01(pedidos, capacidad_peso_kg=0)
    assert val == 0.0
    assert len(sel) == 0


def test_held_karp_tsp_triangulo_retorno():
    # Matriz asimétrica dirigida; el óptimo es 0 -> 2 -> 1 -> 0: 20 m.
    distancias = [
        [0.0, 10.0, 15.0],
        [2.0, 0.0, 9.0],
        [6.0, 3.0, 0.0],
    ]

    ruta_idx, dist, tiempo_ms = held_karp_tsp(distancias, retornar_al_inicio=True)

    # Debe visitar los 3 puntos y retornar al primero
    assert len(ruta_idx) == 4
    assert ruta_idx[0] == 0
    assert ruta_idx[-1] == 0
    assert ruta_idx == [0, 2, 1, 0]
    assert dist == 20.0
    assert tiempo_ms >= 0.0


def test_held_karp_tsp_4_puntos():
    distancias = [
        [0, 4, 8, 7],
        [3, 0, 2, 6],
        [5, 3, 0, 1],
        [2, 7, 4, 0],
    ]
    ruta_idx, dist, _ = held_karp_tsp(distancias, retornar_al_inicio=True)
    assert len(ruta_idx) == 5
    assert ruta_idx[0] == 0 and ruta_idx[-1] == 0
    assert set(ruta_idx[:4]) == {0, 1, 2, 3}
    assert dist == sum(distancias[u][v] for u, v in zip(ruta_idx, ruta_idx[1:]))


def test_mochila_pesos_decimales_no_exceden_capacidad():
    """Regresión: con redondeo al kg, 4.5 kg se contaba como 4 y se excedía la capacidad."""
    pedidos = [
        Pedido("P1", "A", "N01", 0, 0, "S", 1, 4.5, 1.0, 100.0),
        Pedido("P2", "B", "N01", 0, 0, "S", 1, 0.7, 1.0, 90.0),
        Pedido("P3", "C", "N01", 0, 0, "S", 1, 2.2, 1.0, 50.0),
    ]
    valor, sel, _ = resolver_mochila_01(pedidos, capacidad_peso_kg=5)
    assert sum(p.peso_kg for p in sel) <= 5.0
    # 4.5 + 0.7 = 5.2 kg ya no es válido; lo mejor es 0.7 + 2.2 = 2.9 kg o 4.5 sola
    assert valor == 140.0
    assert [p.id for p in sel] == ["P2", "P3"]


def test_mochila_datos_reales_respetan_capacidad():
    from core.gestor_datos import cargar_pedidos
    pedidos = cargar_pedidos()
    for capacidad in (5, 10, 12.5, 15, 25, 35):
        _, sel, _ = resolver_mochila_01(pedidos[:15], capacidad)
        assert sum(p.peso_kg for p in sel) <= capacidad + 1e-9


def test_mochila_coincide_con_fuerza_bruta():
    """El óptimo de la PD es igual al de probar los 2^n subconjuntos (n = 12)."""
    from core.gestor_datos import cargar_pedidos
    pedidos = cargar_pedidos()[:12]
    capacidad = 20
    mejor = 0.0
    for mascara in range(1 << len(pedidos)):
        elegidos = [p for i, p in enumerate(pedidos) if mascara & (1 << i)]
        if sum(p.peso_kg for p in elegidos) <= capacidad + 1e-9:
            mejor = max(mejor, sum(p.valor_soles for p in elegidos))
    valor, _, _ = resolver_mochila_01(pedidos, capacidad)
    assert valor == pytest.approx(mejor)
