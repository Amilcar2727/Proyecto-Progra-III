"""
Pruebas Unitarias para Estructuras de Datos, Ordenación y Búsqueda.
Verifica determinísticamente Merge Sort, Quick Sort, Búsqueda Binaria e Índices.
"""

import pytest
from core.modelos import Pedido
from core.estructuras import (
    merge_sort,
    quick_sort,
    busqueda_binaria,
    construir_indice_id,
    construir_indice_invertido_sector,
)


@pytest.fixture
def pedidos_muestra():
    return [
        Pedido("PED-003", "Café D'Wasi", "N01", -13.5169, -71.9785, "Centro", 2, 1.5, 3.0, 45.0),
        Pedido("PED-001", "Restaurante Cicciolina", "N02", -13.5152, -71.9750, "Centro", 1, 4.5, 8.0, 180.0),
        Pedido("PED-002", "Hotel Monasterio", "N01", -13.5167, -71.9788, "Centro", 1, 2.0, 4.0, 250.0),
        Pedido("PED-004", "Chicharronería", "N04", -13.5194, -71.9835, "San Pedro", 3, 6.0, 10.0, 90.0),
    ]


def test_merge_sort_numeros():
    lista = [38, 27, 43, 3, 9, 82, 10]
    esperado = [3, 9, 10, 27, 38, 43, 82]
    assert merge_sort(lista) == esperado


def test_merge_sort_reverse():
    lista = [1, 5, 2, 8, 3]
    esperado = [8, 5, 3, 2, 1]
    assert merge_sort(lista, reverse=True) == esperado


def test_merge_sort_pedidos_por_valor(pedidos_muestra):
    ordenados = merge_sort(pedidos_muestra, key=lambda p: p.valor_soles, reverse=True)
    valores = [p.valor_soles for p in ordenados]
    assert valores == [250.0, 180.0, 90.0, 45.0]


def test_quick_sort_numeros():
    lista = [10, 7, 8, 9, 1, 5]
    esperado = [1, 5, 7, 8, 9, 10]
    assert quick_sort(lista) == esperado


def test_quick_sort_con_duplicados():
    lista = [4, 2, 2, 8, 3, 3, 1]
    esperado = [1, 2, 2, 3, 3, 4, 8]
    assert quick_sort(lista) == esperado


def test_quick_sort_pedidos_por_prioridad(pedidos_muestra):
    ordenados = quick_sort(pedidos_muestra, key=lambda p: p.prioridad)
    prioridades = [p.prioridad for p in ordenados]
    assert prioridades == [1, 1, 2, 3]


def test_busqueda_binaria_exito_y_fallo():
    arreglo_ordenado = [10, 20, 30, 40, 50, 60]
    assert busqueda_binaria(arreglo_ordenado, 30) == 2
    assert busqueda_binaria(arreglo_ordenado, 10) == 0
    assert busqueda_binaria(arreglo_ordenado, 60) == 5
    assert busqueda_binaria(arreglo_ordenado, 35) == -1
    assert busqueda_binaria(arreglo_ordenado, 5) == -1


def test_busqueda_binaria_en_pedidos(pedidos_muestra):
    pedidos_por_id = quick_sort(pedidos_muestra, key=lambda p: p.id)
    idx = busqueda_binaria(pedidos_por_id, "PED-002", key=lambda p: p.id)
    assert idx != -1
    assert pedidos_por_id[idx].cliente == "Hotel Monasterio"


def test_indices_hash_e_invertido(pedidos_muestra):
    idx_id = construir_indice_id(pedidos_muestra)
    assert "PED-001" in idx_id
    assert idx_id["PED-001"].cliente == "Restaurante Cicciolina"

    idx_sector = construir_indice_invertido_sector(pedidos_muestra)
    assert "Centro" in idx_sector
    assert len(idx_sector["Centro"]) == 3
    assert "San Pedro" in idx_sector
    assert len(idx_sector["San Pedro"]) == 1
