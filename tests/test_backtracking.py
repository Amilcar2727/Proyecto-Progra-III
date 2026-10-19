"""
Pruebas Unitarias para Backtracking con Poda.
Verifica la exploración completa de caminos simples, la poda por cota superior
y el bloqueo dinámico de calles.
"""

import pytest
from core.modelos import Grafo, Nodo
from core.backtracking import buscar_rutas_backtracking


@pytest.fixture
def grafo_diamante():
    r"""
    Grafo en forma de diamante:
         N02 (arriba, largo)
       /     \
     N01      N04
       \     /
         N03 (abajo, corto)
    """
    g = Grafo()
    # Coordenadas aproximadas
    g.agregar_nodo(Nodo("N01", "Origen", -13.5160, -71.9780, "Zona"))
    g.agregar_nodo(Nodo("N02", "Paso Norte", -13.5120, -71.9750, "Zona"))
    g.agregar_nodo(Nodo("N03", "Paso Sur Corto", -13.5170, -71.9760, "Zona"))
    g.agregar_nodo(Nodo("N04", "Destino", -13.5180, -71.9720, "Zona"))

    g.agregar_arista("N01", "N02", 6.0)
    g.agregar_arista("N02", "N04", 6.0)
    g.agregar_arista("N01", "N03", 2.0)
    g.agregar_arista("N03", "N04", 3.0)
    return g


def test_backtracking_dos_rutas_y_optima(grafo_diamante):
    res = buscar_rutas_backtracking(grafo_diamante, "N01", "N04")
    # Existen exactamente dos rutas simples
    assert len(res.rutas_encontradas) == 2
    assert res.ruta_optima is not None

    # La ruta por N03 es más corta que por N02
    assert res.ruta_optima[0] == ["N01", "N03", "N04"]
    assert res.ruta_optima[1] == 5.0
    assert res.rutas_encontradas[0][0] == ["N01", "N03", "N04"]
    assert res.rutas_encontradas[1][0] == ["N01", "N02", "N04"]


def test_backtracking_con_calle_bloqueada(grafo_diamante):
    # Bloquear la vía N01 <-> N03
    grafo_diamante.cambiar_estado_calle("N01", "N03", activa=False)

    res = buscar_rutas_backtracking(grafo_diamante, "N01", "N04")
    # Ahora solo queda 1 ruta viable (por N02)
    assert len(res.rutas_encontradas) == 1
    assert res.ruta_optima[0] == ["N01", "N02", "N04"]


def test_backtracking_sin_conexion(grafo_diamante):
    # Bloquear ambas salidas desde N01
    grafo_diamante.cambiar_estado_calle("N01", "N02", activa=False)
    grafo_diamante.cambiar_estado_calle("N01", "N03", activa=False)

    res = buscar_rutas_backtracking(grafo_diamante, "N01", "N04")
    assert len(res.rutas_encontradas) == 0
    assert res.ruta_optima is None


def test_backtracking_poda_por_costo():
    from core.gestor_datos import cargar_grafo
    g = cargar_grafo()
    res = buscar_rutas_backtracking(g, "N01", "N15")
    # En un recorrido largo en la red de Cusco, debe haber podas efectivas por cota
    assert res.total_ramas_podadas > 0
    assert res.ruta_optima is not None
