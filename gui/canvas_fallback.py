"""
Módulo de Fallback Fuera de Línea (Offline Canvas Fallback).
Permite renderizar el grafo vial, rutas, pedidos y marcadores usando un Canvas nativo de Tkinter
cuando no hay conexión a internet o fallan los tiles de OpenStreetMap/Google.
"""

import tkinter as tk
from typing import Callable, Dict, List, Optional, Tuple


class CanvasFallback(tk.Canvas):
    """
    Lienzo vectorial 2D que proyecta coordenadas geográficas (lat, lon) a píxeles.
    Garantiza que la aplicación nunca se caiga ante fallos de red.
    """

    def __init__(self, master, *args, **kwargs):
        # closeenough: tolerancia en píxeles para que una calle de 2 px sea fácil de clicar.
        super().__init__(
            master, bg="#f8fafc", highlightthickness=0, closeenough=4, *args, **kwargs
        )
        self.marcadores: List[dict] = []
        self.caminos: List[dict] = []
        self.callbacks_click: List[Callable] = []
        self._lineas_clicables: set = set()
        self._redibujo_pendiente = False

        # Rango geográfico predeterminado de Cusco para normalización
        self.min_lat = -13.5450
        self.max_lat = -13.5050
        self.min_lon = -71.9900
        self.max_lon = -71.9000

        self.bind("<Configure>", self._al_redimensionar)
        self.bind("<Button-1>", self._al_hacer_clic)

    def fijar_limites_geograficos(
        self, min_lat: float, max_lat: float, min_lon: float, max_lon: float
    ):
        """Ajusta la caja envolvente (bounding box) para centrar los nodos."""
        margen_lat = (max_lat - min_lat) * 0.1 or 0.01
        margen_lon = (max_lon - min_lon) * 0.1 or 0.01
        self.min_lat = min_lat - margen_lat
        self.max_lat = max_lat + margen_lat
        self.min_lon = min_lon - margen_lon
        self.max_lon = max_lon + margen_lon
        self._programar_redibujo()

    def geo_a_pixel(self, lat: float, lon: float) -> Tuple[float, float]:
        """Normaliza (lat, lon) al espacio de píxeles del Canvas."""
        w = max(self.winfo_width(), 400)
        h = max(self.winfo_height(), 300)
        padding = 40

        # En latitud, mayor valor está más al norte (arriba en pantalla -> menor Y)
        norm_x = (lon - self.min_lon) / max((self.max_lon - self.min_lon), 0.0001)
        norm_y = (self.max_lat - lat) / max((self.max_lat - self.min_lat), 0.0001)

        px = padding + norm_x * (w - 2 * padding)
        py = padding + norm_y * (h - 2 * padding)
        return px, py

    def pixel_a_geo(self, px: float, py: float) -> Tuple[float, float]:
        """Convierte píxeles de vuelta a coordenadas geográficas estimadas."""
        w = max(self.winfo_width(), 400)
        h = max(self.winfo_height(), 300)
        padding = 40

        norm_x = (px - padding) / max((w - 2 * padding), 1)
        norm_y = (py - padding) / max((h - 2 * padding), 1)

        lon = self.min_lon + norm_x * (self.max_lon - self.min_lon)
        lat = self.max_lat - norm_y * (self.max_lat - self.min_lat)
        return lat, lon

    def set_position(self, lat: float, lon: float):
        """Compatibilidad con TkinterMapView."""
        pass

    def set_zoom(self, zoom: int):
        """Compatibilidad con TkinterMapView."""
        pass

    def set_marker(
        self,
        lat: float,
        lon: float,
        text: Optional[str] = None,
        marker_color_circle: str = "#2563eb",
        text_color: str = "#1e293b",
        command: Optional[Callable] = None,
        data: any = None,
        **kwargs,
    ):
        """Crea un marcador circular con etiqueta en el lienzo."""
        marcador = {
            "lat": lat,
            "lon": lon,
            "text": text or "",
            "color": marker_color_circle,
            "text_color": text_color,
            "command": command,
            "data": data,
        }
        self.marcadores.append(marcador)
        self._programar_redibujo()
        return marcador

    def set_path(
        self,
        position_list: List[Tuple[float, float]],
        color: str = "#9ca3af",
        width: int = 2,
        command: Optional[Callable] = None,
        data: any = None,
        **kwargs,
    ):
        """Crea una polilínea o arista entre una lista de puntos geográficos."""
        camino = {
            "puntos": position_list,
            "color": color,
            "width": width,
            "command": command,
            "data": data,
        }
        self.caminos.append(camino)
        self._programar_redibujo()
        return camino

    def delete_all_marker(self):
        """Limpia todos los marcadores."""
        self.marcadores.clear()
        self._programar_redibujo()

    def delete_all_path(self):
        """Limpia todos los caminos."""
        self.caminos.clear()
        self._programar_redibujo()

    def add_left_click_map_command(self, callback: Callable):
        """Registra callback al hacer clic en el mapa."""
        self.callbacks_click.append(callback)

    def _programar_redibujo(self):
        """
        Agrupa muchos set_path/set_marker seguidos en un único redibujo.
        Antes se redibujaba todo el lienzo en cada llamada: O(k²) para k elementos.
        """
        if not self._redibujo_pendiente:
            self._redibujo_pendiente = True
            self.after_idle(self.redibujar)

    def _al_redimensionar(self, event):
        self._programar_redibujo()

    def _al_hacer_clic(self, event):
        # Un clic sobre una calle ya lo atiende su propio manejador; no crear pedido.
        actuales = set(self.find_withtag("current"))
        if actuales & self._lineas_clicables:
            return
        lat, lon = self.pixel_a_geo(event.x, event.y)
        # Notificar a los listeners del mapa
        for cb in self.callbacks_click:
            cb((lat, lon))

    def redibujar(self):
        """Limpia el canvas y vuelve a trazar caminos y marcadores con las dimensiones actuales."""
        self._redibujo_pendiente = False
        self.delete("all")
        self._lineas_clicables = set()

        # Marca de agua indicando modo fuera de línea
        self.create_text(
            15,
            15,
            anchor="nw",
            text="Modo sin conexión: mapa vectorial (Canvas 2D)",
            font=("Segoe UI", 9, "bold"),
            fill="#94a3b8",
        )

        # 1. Dibujar aristas/caminos
        for c in self.caminos:
            puntos_px = []
            for lat, lon in c["puntos"]:
                x, y = self.geo_a_pixel(lat, lon)
                puntos_px.extend([x, y])
            if len(puntos_px) >= 4:
                line_id = self.create_line(
                    *puntos_px,
                    fill=c["color"],
                    width=c["width"],
                    capstyle=tk.ROUND,
                    joinstyle=tk.ROUND,
                )
                if c["command"]:
                    self._lineas_clicables.add(line_id)
                    self.tag_bind(line_id, "<Button-1>", lambda e, cam=c: cam["command"](cam))
                    self.tag_bind(line_id, "<Enter>", lambda e: self.config(cursor="hand2"))
                    self.tag_bind(line_id, "<Leave>", lambda e: self.config(cursor=""))

        # 2. Dibujar marcadores (nodos)
        radio = 7
        for m in self.marcadores:
            x, y = self.geo_a_pixel(m["lat"], m["lon"])
            tag = f"m_{id(m)}"
            # Círculo exterior blanco para contraste
            self.create_oval(
                x - radio - 1,
                y - radio - 1,
                x + radio + 1,
                y + radio + 1,
                fill="#ffffff",
                outline="#cbd5e1",
                width=1,
                tags=tag,
            )
            # Círculo interior con color
            self.create_oval(
                x - radio,
                y - radio,
                x + radio,
                y + radio,
                fill=m["color"],
                outline="",
                tags=tag,
            )
            # Etiqueta de texto
            if m["text"]:
                # Halo blanco detrás del texto para que se lea sobre las calles
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    self.create_text(
                        x + dx, y - radio - 7 + dy, text=m["text"],
                        font=("Segoe UI", 8, "bold"), fill="#f8fafc", tags=tag,
                    )
                self.create_text(
                    x,
                    y - radio - 7,
                    text=m["text"],
                    font=("Segoe UI", 8, "bold"),
                    fill=m.get("text_color", "#1e293b"),
                    tags=tag,
                )
            if m["command"]:
                self.tag_bind(tag, "<Button-1>", lambda e, marc=m: marc["command"](marc))
