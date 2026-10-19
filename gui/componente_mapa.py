"""
Módulo de Componente de Mapa Reutilizable.
Encapsula TkinterMapView y realiza conmutación transparente a CanvasFallback
si no hay conexión o se produce un error en la carga de tiles.
"""

import os
import socket
import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Optional, Tuple
import config
from core.grafo import geometria_de_ruta
from core.modelos import Grafo

try:
    import tkintermapview
    TIKINTER_MAP_VIEW_DISPONIBLE = True
except ImportError:
    TIKINTER_MAP_VIEW_DISPONIBLE = False

from gui.canvas_fallback import CanvasFallback

_HAY_INTERNET: Optional[bool] = None


def hay_conexion_tiles() -> bool:
    """
    Comprueba UNA vez (y guarda el resultado) si el servidor de tiles responde.
    Sin conexión, TkinterMapView mostraría un fondo gris vacío; en ese caso se usa
    directamente el Canvas vectorial. Forzar modo offline: RUTAS_OFFLINE=1.
    """
    global _HAY_INTERNET
    if os.environ.get("RUTAS_OFFLINE") == "1":
        return False
    if _HAY_INTERNET is None:
        try:
            with socket.create_connection(("tile.openstreetmap.org", 443), timeout=1.5):
                _HAY_INTERNET = True
        except OSError:
            _HAY_INTERNET = False
    return _HAY_INTERNET


class ComponenteMapa(ttk.Frame):
    """
    Componente visual que dibuja el grafo de Cusco, marcadores de pedidos,
    calles transitables / bloqueadas y rutas calculadas por los algoritmos.
    """

    def __init__(
        self,
        master,
        grafo: Optional[Grafo] = None,
        al_hacer_clic_arista: Optional[Callable[[str, str], None]] = None,
        al_hacer_clic_mapa: Optional[Callable[[Tuple[float, float]], None]] = None,
        *args,
        **kwargs,
    ):
        super().__init__(master, *args, **kwargs)
        self.grafo = grafo
        self.al_hacer_clic_arista = al_hacer_clic_arista
        self.al_hacer_clic_mapa = al_hacer_clic_mapa

        self.modo_fallback = False
        self.widget_mapa = None
        self.marcadores_dict = {}
        self.caminos_grafo_dict = {}
        self.caminos_rutas_lista = []
        self.version_dibujada = -1

        self._crear_widget_mapa()

    def _crear_widget_mapa(self):
        """Inicializa TkinterMapView o salta a CanvasFallback si falla."""
        if TIKINTER_MAP_VIEW_DISPONIBLE and hay_conexion_tiles():
            try:
                mapa = tkintermapview.TkinterMapView(
                    self,
                    corner_radius=0,
                    width=400,
                    height=400,
                )
                mapa.set_tile_server(config.TILE_PROVIDER_ACTUAL, max_zoom=config.MAX_ZOOM)
                mapa.set_position(config.MAPA_CENTRO_LAT, config.MAPA_CENTRO_LON)
                mapa.set_zoom(config.MAPA_ZOOM_INICIAL)

                if self.al_hacer_clic_mapa:
                    mapa.add_left_click_map_command(self.al_hacer_clic_mapa)

                mapa.pack(fill=tk.BOTH, expand=True)
                self.widget_mapa = mapa
                self.modo_fallback = False
                self._mostrar_atribucion_osm()
                return
            except Exception as e:
                print(f"[Aviso] No se pudo iniciar TkinterMapView ({e}). Usando CanvasFallback.")

        # Fallback a Canvas nativo
        self.widget_mapa = CanvasFallback(self)
        if self.al_hacer_clic_mapa:
            self.widget_mapa.add_left_click_map_command(self.al_hacer_clic_mapa)
        self.widget_mapa.pack(fill=tk.BOTH, expand=True)
        self.modo_fallback = True
        self._mostrar_atribucion_osm()

    def _mostrar_atribucion_osm(self):
        ttk.Label(
            self,
            text="© OpenStreetMap contributors",
            font=("Segoe UI", 8),
            foreground="#475569",
            anchor="e",
        ).pack(side=tk.BOTTOM, fill=tk.X, padx=6)

    def cambiar_proveedor_tiles(self, url_tile: str):
        """Cambia entre OpenStreetMap y Google Tiles."""
        if not self.modo_fallback and hasattr(self.widget_mapa, "set_tile_server"):
            try:
                self.widget_mapa.set_tile_server(url_tile, max_zoom=config.MAX_ZOOM)
            except Exception as e:
                print(f"Error al cambiar tiles: {e}")

    def centrar(self, lat: float = config.MAPA_CENTRO_LAT, lon: float = config.MAPA_CENTRO_LON, zoom: int = 14):
        """Centra la vista del mapa en una coordenada."""
        if hasattr(self.widget_mapa, "set_position"):
            self.widget_mapa.set_position(lat, lon)
        if hasattr(self.widget_mapa, "set_zoom"):
            self.widget_mapa.set_zoom(zoom)

    def limpiar_rutas(self):
        """Elimina solo las rutas resaltadas en el mapa."""
        for path_obj in self.caminos_rutas_lista:
            try:
                if hasattr(path_obj, "delete"):
                    path_obj.delete()
            except Exception:
                pass
        self.caminos_rutas_lista.clear()
        if self.modo_fallback:
            self.widget_mapa.delete_all_path()
            # Restaurar aristas del grafo
            if self.grafo:
                self.dibujar_grafo()

    def limpiar_todo(self):
        """Limpia marcadores y rutas."""
        if hasattr(self.widget_mapa, "delete_all_marker"):
            self.widget_mapa.delete_all_marker()
        if hasattr(self.widget_mapa, "delete_all_path"):
            self.widget_mapa.delete_all_path()
        self.marcadores_dict.clear()
        self.caminos_grafo_dict.clear()
        self.caminos_rutas_lista.clear()

    def dibujar_grafo(self, resaltar_aristas_bloqueadas: bool = True):
        """
        Dibuja los nodos y aristas de la red vial de Cusco.
        Las aristas activas se muestran en gris; las bloqueadas en rojo intenso.
        """
        if not self.grafo:
            return

        self.limpiar_todo()
        self.version_dibujada = self.grafo.version

        # Ajustar límites geográficos para Canvas si estamos en fallback
        if self.modo_fallback:
            lats = [n.lat for n in self.grafo.nodos.values()]
            lons = [n.lon for n in self.grafo.nodos.values()]
            if lats and lons:
                self.widget_mapa.fijar_limites_geograficos(
                    min(lats), max(lats), min(lons), max(lons)
                )

        # 1. Dibujar aristas
        for arista in self.grafo.todas_las_aristas():
            color = config.COLOR_CALLE_BLOQUEADA if not arista.activa else config.COLOR_CALLE_NORMAL
            ancho = 4 if not arista.activa else 2

            puntos = arista.geometria
            if len(puntos) < 2:
                raise ValueError(
                    f"El arco {arista.origen_id}->{arista.destino_id} no tiene geometría vial."
                )

            def _click_handler(path, u_id=arista.origen_id, v_id=arista.destino_id):
                if self.al_hacer_clic_arista:
                    self.al_hacer_clic_arista(u_id, v_id)

            path_obj = self.widget_mapa.set_path(
                position_list=puntos,
                color=color,
                width=ancho,
                command=_click_handler,
                data=(arista.origen_id, arista.destino_id),
            )
            par_clave = (arista.origen_id, arista.destino_id)
            self.caminos_grafo_dict[par_clave] = path_obj

        # Señal "CERRADA" en el punto medio de cada calle cerrada (una por calle)
        for u, v in self.grafo.calles_cerradas():
            arista = self.grafo.adyacencia.get(u, {}).get(v) or self.grafo.adyacencia[v][u]
            lat, lon = arista.geometria[len(arista.geometria) // 2]
            self.widget_mapa.set_marker(
                lat, lon, text=f"✖ CERRADA {u}–{v}",
                marker_color_circle=config.COLOR_CALLE_BLOQUEADA, text_color="#b91c1c",
            )

        # 2. Dibujar nodos
        for nodo_id, nodo in self.grafo.nodos.items():
            marcador = self.widget_mapa.set_marker(
                nodo.lat,
                nodo.lon,
                text=f"{nodo.id}: {nodo.nombre}",
                marker_color_circle=config.COLOR_NODO_DEFECTO,
                text_color="#0f172a",
                data=nodo_id,
            )
            self.marcadores_dict[nodo_id] = marcador

    def esta_desactualizado(self) -> bool:
        """True si el grafo cambió (p. ej. una calle cerrada) desde el último dibujo."""
        return self.grafo is not None and self.version_dibujada != self.grafo.version

    def resaltar_ruta(
        self,
        secuencia_nodos: List[str],
        color: str = config.COLOR_RUTA_GREEDY,
        ancho: int = 5,
        nombre_ruta: str = "",
    ):
        """
        Dibuja una ruta calculada entre una secuencia ordenada de nodos.
        """
        if not self.grafo or len(secuencia_nodos) < 2:
            return

        puntos = geometria_de_ruta(self.grafo, secuencia_nodos)

        if len(puntos) >= 2:
            path_obj = self.widget_mapa.set_path(
                position_list=puntos,
                color=color,
                width=ancho,
                name=nombre_ruta,
            )
            self.caminos_rutas_lista.append(path_obj)

    def resaltar_camino_aristas(
        self,
        camino: List[str],
        color: str = config.COLOR_RUTA_BACKTRACKING,
        ancho: int = 5,
        nombre_ruta: str = "",
    ):
        """
        Dibuja un camino usando EXACTAMENTE las aristas u->v que lo forman.
        (resaltar_ruta, en cambio, une paradas por el camino mínimo de Dijkstra, que
        entre dos lugares vecinos podría no ser la arista directa.) Lo usa Backtracking.
        """
        if not self.grafo or len(camino) < 2:
            return
        puntos: List[Tuple[float, float]] = []
        for u, v in zip(camino, camino[1:]):
            geometria = self.grafo.adyacencia[u][v].geometria
            if puntos and puntos[-1] == geometria[0]:
                puntos.extend(geometria[1:])
            else:
                puntos.extend(geometria)
        if len(puntos) >= 2:
            self.caminos_rutas_lista.append(
                self.widget_mapa.set_path(
                    position_list=puntos, color=color, width=ancho, name=nombre_ruta
                )
            )

    def agregar_marcador_pedido(
        self,
        lat: float,
        lon: float,
        etiqueta: str,
        color: str = "#e11d48",
    ):
        """Agrega un marcador especial para un pedido de cliente."""
        marcador = self.widget_mapa.set_marker(
            lat,
            lon,
            text=etiqueta,
            marker_color_circle=color,
            text_color="#991b1b",
        )
        return marcador
