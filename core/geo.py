"""
Módulo de Utilidades Geográficas.
Implementación matemática de la fórmula de Haversine para distancias ortodrómicas en la esfera terrestre.
"""

import math
from typing import Tuple

# Radio medio de la Tierra en metros (WGS84 aproximado)
RADIO_TIERRA_METROS = 6371000.0


def distancia_haversine(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calcula la distancia de círculo máximo entre dos puntos geográficos (lat, lon)
    en metros usando la fórmula de Haversine.

    Paradigmas/Conceptos: Trigonometría esférica.
    Complejidad Temporal: O(1) operaciones aritméticas.
    Complejidad Espacial: O(1).

    :param lat1: Latitud del punto 1 en grados decimales.
    :param lon1: Longitud del punto 1 en grados decimales.
    :param lat2: Latitud del punto 2 en grados decimales.
    :param lon2: Longitud del punto 2 en grados decimales.
    :return: Distancia en metros (float redondeado a 2 decimales).
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
    )
    # Evita posibles inconsistencias por imprecisión de punto flotante (> 1.0)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))

    return round(RADIO_TIERRA_METROS * c, 2)


def centroide(puntos: list[Tuple[float, float]]) -> Tuple[float, float]:
    """
    Calcula el centroide medio de una lista de coordenadas (lat, lon).
    Complejidad: O(n).
    """
    if not puntos:
        return (-13.5167, -71.9788)
    sum_lat = sum(p[0] for p in puntos)
    sum_lon = sum(p[1] for p in puntos)
    n = len(puntos)
    return (sum_lat / n, sum_lon / n)
