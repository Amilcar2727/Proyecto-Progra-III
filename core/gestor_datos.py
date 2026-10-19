"""
Módulo de Gestión de Carga y Persistencia de Datos.
Lee y guarda entidades (Nodos, Aristas, Pedidos, Repartidores) desde y hacia archivos JSON.
"""

import json
from pathlib import Path
from typing import List, Tuple
from config import NODOS_FILE, PEDIDOS_FILE, REPARTIDORES_FILE
from core.modelos import Grafo, Nodo, Pedido, Repartidor


def cargar_grafo(ruta_json: Path = NODOS_FILE) -> Grafo:
    """
    Lee el archivo de nodos y aristas de Cusco y construye el objeto Grafo.
    Calcula distancias geográficas reales mediante Haversine para cada arista.
    """
    grafo = Grafo()
    if not ruta_json.exists():
        raise FileNotFoundError(f"No se encontró el archivo de grafo en: {ruta_json}")

    with open(ruta_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data.get("nodos", []):
        nodo = Nodo(
            id=item["id"],
            nombre=item["nombre"],
            lat=float(item["lat"]),
            lon=float(item["lon"]),
            sector=item["sector"],
        )
        grafo.agregar_nodo(nodo)

    for u, v in data.get("aristas", []):
        grafo.agregar_arista(u, v, bidireccional=True)

    return grafo


def cargar_pedidos(ruta_json: Path = PEDIDOS_FILE) -> List[Pedido]:
    """Carga los pedidos de entrega desde JSON."""
    if not ruta_json.exists():
        return []

    with open(ruta_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    pedidos = []
    for item in data:
        p = Pedido(
            id=item["id"],
            cliente=item["cliente"],
            nodo_id=item["nodo_id"],
            lat=float(item["lat"]),
            lon=float(item["lon"]),
            sector=item["sector"],
            prioridad=int(item["prioridad"]),
            peso_kg=float(item["peso_kg"]),
            volumen_l=float(item["volumen_l"]),
            valor_soles=float(item["valor_soles"]),
        )
        pedidos.append(p)
    return pedidos


def guardar_pedidos(pedidos: List[Pedido], ruta_json: Path = PEDIDOS_FILE) -> None:
    """Serializa la lista de pedidos en JSON."""
    data = []
    for p in pedidos:
        data.append(
            {
                "id": p.id,
                "cliente": p.cliente,
                "nodo_id": p.nodo_id,
                "lat": p.lat,
                "lon": p.lon,
                "sector": p.sector,
                "prioridad": p.prioridad,
                "peso_kg": p.peso_kg,
                "volumen_l": p.volumen_l,
                "valor_soles": p.valor_soles,
            }
        )
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def cargar_repartidores(ruta_json: Path = REPARTIDORES_FILE) -> List[Repartidor]:
    """Carga la flota de repartidores desde JSON."""
    if not ruta_json.exists():
        return []

    with open(ruta_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    repartidores = []
    for item in data:
        r = Repartidor(
            id=item["id"],
            nombre=item["nombre"],
            tipo_vehiculo=item["tipo_vehiculo"],
            nodo_inicio_id=item["nodo_inicio_id"],
            cap_peso_kg=float(item["cap_peso_kg"]),
            cap_vol_l=float(item["cap_vol_l"]),
        )
        repartidores.append(r)
    return repartidores
