"""
Módulo de Estructuras de Datos, Ordenación y Búsqueda (Implementación Manual Pura).
Prohibido el uso de sorted() o .sort() de la biblioteca estándar de Python.
Todos los algoritmos están implementados artesanalmente para evaluación académica en UNSAAC.
"""

from typing import Any, Callable, Dict, List, Optional, TypeVar
from core.modelos import Pedido

T = TypeVar("T")


def merge_sort(
    lista: List[T],
    key: Optional[Callable[[T], Any]] = None,
    reverse: bool = False,
) -> List[T]:
    """
    Ordenamiento por Mezcla (Merge Sort) implementado a mano.
    
    Paradigma: Divide y Vencerás (D&C).
    Idea: Divide la lista recursivamente en dos mitades de tamaño n/2,
          ordena cada mitad recursivamente y las combina (mezcla) en orden.
    
    Complejidad Temporal:
      - Mejor caso:    O(n log n)
      - Caso promedio: O(n log n)
      - Peor caso:     O(n log n)
      Justificación: La división toma profundidad log2(n) y en cada nivel
      se recorren todos los n elementos para combinarlos.
    
    Complejidad Espacial:
      - O(n) memoria auxiliar para alojar los subarreglos durante la mezcla.
    
    :param lista: Lista de elementos a ordenar.
    :param key: Función para extraer la clave de comparación de cada elemento.
    :param reverse: True para orden descendente, False para ascendente.
    :return: Nueva lista ordenada.
    """
    n = len(lista)
    if n <= 1:
        return list(lista)

    medio = n // 2
    izquierda = merge_sort(lista[:medio], key=key, reverse=reverse)
    derecha = merge_sort(lista[medio:], key=key, reverse=reverse)

    return _mezclar(izquierda, derecha, key=key, reverse=reverse)


def _mezclar(
    izq: List[T],
    der: List[T],
    key: Optional[Callable[[T], Any]] = None,
    reverse: bool = False,
) -> List[T]:
    """Combina dos listas ordenadas en una sola lista ordenada en O(n)."""
    resultado: List[T] = []
    i = 0
    j = 0
    len_izq = len(izq)
    len_der = len(der)

    def _val(x: T):
        return key(x) if key is not None else x

    while i < len_izq and j < len_der:
        val_i = _val(izq[i])
        val_j = _val(der[j])

        condicion = (val_i >= val_j) if reverse else (val_i <= val_j)
        if condicion:
            resultado.append(izq[i])
            i += 1
        else:
            resultado.append(der[j])
            j += 1

    # Agregar elementos restantes
    while i < len_izq:
        resultado.append(izq[i])
        i += 1
    while j < len_der:
        resultado.append(der[j])
        j += 1

    return resultado


def quick_sort(
    lista: List[T],
    key: Optional[Callable[[T], Any]] = None,
    reverse: bool = False,
) -> List[T]:
    """
    Ordenamiento Rápido (Quick Sort) implementado a mano con partición de Lomuto
    y selección de pivote por mediana de tres para mitigar casos desfavorables.

    Paradigma: Divide y Vencerás (D&C).
    Idea: Selecciona un elemento pivote, particiona el arreglo de modo que los elementos
          menores queden a un lado y los mayores al otro, y aplica recursión.

    Complejidad Temporal:
      - Mejor caso:    O(n log n) (partición equilibrada n/2)
      - Caso promedio: O(n log n)
      - Peor caso:     O(n²) (particiones desbalanceadas 1 y n-1)
    
    Complejidad Espacial:
      - O(log n) en promedio por llamadas en la pila de recursión (O(n) en peor caso).

    :param lista: Lista a ordenar.
    :param key: Función extractora de clave.
    :param reverse: True para orden descendente, False para ascendente.
    :return: Nueva lista ordenada.
    """
    copia = list(lista)
    _quick_sort_recursivo(copia, 0, len(copia) - 1, key=key, reverse=reverse)
    return copia


def _quick_sort_recursivo(
    arr: List[T],
    bajo: int,
    alto: int,
    key: Optional[Callable[[T], Any]] = None,
    reverse: bool = False,
) -> None:
    """Función auxiliar in-place para Quick Sort."""
    if bajo < alto:
        pivote_idx = _particion(arr, bajo, alto, key=key, reverse=reverse)
        _quick_sort_recursivo(arr, bajo, pivote_idx - 1, key=key, reverse=reverse)
        _quick_sort_recursivo(arr, pivote_idx + 1, alto, key=key, reverse=reverse)


def _particion(
    arr: List[T],
    bajo: int,
    alto: int,
    key: Optional[Callable[[T], Any]] = None,
    reverse: bool = False,
) -> int:
    """Partición de Lomuto con pivote al final."""
    def _val(x: T):
        return key(x) if key is not None else x

    # Heurística simple de mediana de tres para bajo, medio y alto
    medio = (bajo + alto) // 2
    if _comparar(_val(arr[medio]), _val(arr[bajo]), reverse):
        arr[bajo], arr[medio] = arr[medio], arr[bajo]
    if _comparar(_val(arr[alto]), _val(arr[bajo]), reverse):
        arr[bajo], arr[alto] = arr[alto], arr[bajo]
    if _comparar(_val(arr[alto]), _val(arr[medio]), reverse):
        arr[medio], arr[alto] = arr[alto], arr[medio]

    val_pivote = _val(arr[alto])
    i = bajo - 1

    for j in range(bajo, alto):
        val_j = _val(arr[j])
        condicion = (val_j >= val_pivote) if reverse else (val_j <= val_pivote)
        if condicion:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]

    arr[i + 1], arr[alto] = arr[alto], arr[i + 1]
    return i + 1


def _comparar(val_a: Any, val_b: Any, reverse: bool) -> bool:
    return (val_a > val_b) if reverse else (val_a < val_b)


def busqueda_binaria(
    lista_ordenada: List[T],
    valor_objetivo: Any,
    key: Optional[Callable[[T], Any]] = None,
) -> int:
    """
    Búsqueda Binaria manual sobre una lista ordenada.

    Paradigma: Disminuye y Vencerás (Decrease and Conquer).
    Idea: Compara el objetivo con el elemento central. Si no coincide, descarta
          la mitad donde no puede estar y continúa en la mitad restante.

    Complejidad Temporal:
      - O(log n) en todos los casos de búsqueda no trivial.
    Complejidad Espacial:
      - O(1) implementación iterativa.

    :param lista_ordenada: Lista preordenada según la clave.
    :param valor_objetivo: Valor buscado.
    :param key: Función para extraer la clave de cada elemento.
    :return: Índice del elemento si se encuentra, o -1 si no existe.
    """
    izq = 0
    der = len(lista_ordenada) - 1

    while izq <= der:
        medio = (izq + der) // 2
        item = lista_ordenada[medio]
        val_medio = key(item) if key is not None else item

        if val_medio == valor_objetivo:
            return medio
        elif val_medio < valor_objetivo:
            izq = medio + 1
        else:
            der = medio - 1

    return -1


def construir_indice_id(pedidos: List[Pedido]) -> Dict[str, Pedido]:
    """
    Construye una tabla hash / diccionario mapeando ID -> Pedido.
    Complejidad de construcción: O(n) tiempo y espacio.
    Complejidad de consulta: O(1) promedio.
    """
    indice: Dict[str, Pedido] = {}
    for p in pedidos:
        indice[p.id] = p
    return indice


def construir_indice_invertido_sector(pedidos: List[Pedido]) -> Dict[str, List[Pedido]]:
    """
    Construye un índice invertido mapeando Sector -> Lista de Pedidos en ese sector.
    Complejidad de construcción: O(n) tiempo y espacio.
    Complejidad de consulta: O(1) para recuperar la lista de un sector.
    """
    indice: Dict[str, List[Pedido]] = {}
    for p in pedidos:
        sector_norm = p.sector.strip()
        if sector_norm not in indice:
            indice[sector_norm] = []
        indice[sector_norm].append(p)
    return indice
