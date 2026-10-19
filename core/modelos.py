"""
Módulo de Modelos y Estructuras de Datos del Dominio.
Define las dataclasses para Nodos, Aristas, Grafo de Cusco, Pedidos y Repartidores.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from core.geo import distancia_haversine


@dataclass
class Nodo:
    """Representa un punto de referencia en la ciudad de Cusco."""
    id: str
    nombre: str
    lat: float
    lon: float
    sector: str

    def coordenadas(self) -> Tuple[float, float]:
        return (self.lat, self.lon)


@dataclass
class Arista:
    """Representa un tramo vial entre dos nodos de la red."""
    origen_id: str
    destino_id: str
    distancia_m: float
    activa: bool = True  # True = transitable, False = calle bloqueada por obras/tráfico


@dataclass
class Pedido:
    """Representa un pedido de reparto solicitado por un cliente."""
    id: str
    cliente: str
    nodo_id: str
    lat: float
    lon: float
    sector: str
    prioridad: int        # 1: Alta (Urgente), 2: Media, 3: Normal
    peso_kg: float
    volumen_l: float
    valor_soles: float

    def coordenadas(self) -> Tuple[float, float]:
        return (self.lat, self.lon)


@dataclass
class Repartidor:
    """Representa un repartidor disponible en la flota."""
    id: str
    nombre: str
    tipo_vehiculo: str     # 'Bicicleta', 'Motocicleta', 'Furgón'
    nodo_inicio_id: str
    cap_peso_kg: float
    cap_vol_l: float
    nodo_actual_id: Optional[str] = None

    def __post_init__(self):
        if self.nodo_actual_id is None:
            self.nodo_actual_id = self.nodo_inicio_id


@dataclass
class Ruta:
    """Representa el resultado de una planificación de ruta."""
    secuencia_nodos: List[str] = field(default_factory=list)
    pedidos_cubiertos: List[str] = field(default_factory=list)
    distancia_total_m: float = 0.0
    algoritmo_utilizado: str = ""
    tiempo_computo_ms: float = 0.0


class Grafo:
    """
    Grafo que representa la red vial de Cusco.
    Implementado con listas/diccionarios de adyacencia propios.
    """

    def __init__(self):
        self.nodos: Dict[str, Nodo] = {}
        # adyacencia[u][v] = Arista(u, v, distancia, activa)
        self.adyacencia: Dict[str, Dict[str, Arista]] = {}

    def agregar_nodo(self, nodo: Nodo) -> None:
        """Agrega un nodo al grafo e inicializa su lista de adyacencia."""
        self.nodos[nodo.id] = nodo
        if nodo.id not in self.adyacencia:
            self.adyacencia[nodo.id] = {}

    def agregar_arista(
        self, origen_id: str, destino_id: str, bidireccional: bool = True
    ) -> None:
        """
        Agrega una arista entre dos nodos calculando su peso mediante Haversine.
        """
        if origen_id not in self.nodos or destino_id not in self.nodos:
            raise ValueError(f"Nodos {origen_id} o {destino_id} no existen en el grafo.")

        nodo_u = self.nodos[origen_id]
        nodo_v = self.nodos[destino_id]
        distancia = distancia_haversine(nodo_u.lat, nodo_u.lon, nodo_v.lat, nodo_v.lon)

        arista_uv = Arista(origen_id, destino_id, distancia, activa=True)
        self.adyacencia[origen_id][destino_id] = arista_uv

        if bidireccional:
            arista_vu = Arista(destino_id, origen_id, distancia, activa=True)
            self.adyacencia[destino_id][origen_id] = arista_vu

    def obtener_vecinos_activos(self, nodo_id: str) -> List[Tuple[str, float]]:
        """
        Retorna los vecinos transitables (aristas activas) y su distancia.
        Complejidad: O(grado(nodo_id)).
        """
        if nodo_id not in self.adyacencia:
            return []
        vecinos = []
        for destino_id, arista in self.adyacencia[nodo_id].items():
            if arista.activa:
                vecinos.append((destino_id, arista.distancia_m))
        return vecinos

    def cambiar_estado_calle(
        self, u: str, v: str, activa: bool, bidireccional: bool = True
    ) -> bool:
        """Permite bloquear o reabrir una calle."""
        modificado = False
        if u in self.adyacencia and v in self.adyacencia[u]:
            self.adyacencia[u][v].activa = activa
            modificado = True
        if bidireccional and v in self.adyacencia and u in self.adyacencia[v]:
            self.adyacencia[v][u].activa = activa
            modificado = True
        return modificado

    def esta_bloqueada(self, u: str, v: str) -> bool:
        """Verifica si la calle entre u y v está bloqueada."""
        if u in self.adyacencia and v in self.adyacencia[u]:
            return not self.adyacencia[u][v].activa
        return False

    def todas_las_aristas(self) -> List[Arista]:
        """Retorna lista única de aristas (evitando duplicar bidireccionales)."""
        aristas = []
        vistos = set()
        for u in self.adyacencia:
            for v, arista in self.adyacencia[u].items():
                par = tuple(sorted([u, v]))
                if par not in vistos:
                    vistos.add(par)
                    aristas.append(arista)
        return aristas
