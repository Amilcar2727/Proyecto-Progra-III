"""
Pestaña de Visualización y Gestión de la Red Vial de Cusco.
Permite inspeccionar el grafo, bloquear/reabrir calles interactivamente y conmutar proveedores de mapa.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional, Tuple
import config
from core.geo import distancia_haversine
from core.modelos import Grafo
from gui.componente_mapa import ComponenteMapa
from gui.panel_desplazable import crear_panel_lateral


class TabMapa(ttk.Frame):
    """Pestaña para visualizar la red vial de Cusco y controlar el estado de las vías."""

    def __init__(
        self,
        master,
        grafo: Grafo,
        al_hacer_clic_mapa: Optional[
            Callable[[Tuple[float, float]], None]
        ] = None,
        *args,
        **kwargs,
    ):
        super().__init__(master, *args, **kwargs)
        self.grafo = grafo
        self.al_hacer_clic_mapa = al_hacer_clic_mapa

        self._crear_interfaz()
        self.actualizar_estadisticas()

    def _crear_interfaz(self):
        # Panel lateral izquierdo (Controles y estadísticas)
        panel_izq = crear_panel_lateral(self, ancho=320, padding=12)

        # Título y descripción
        ttk.Label(
            panel_izq,
            text="Red Vial de Cusco",
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="w", pady=(0, 4))

        ttk.Label(
            panel_izq,
            text="Grafo disperso de lugares de interés. Haz clic en una conexión para cerrarla en ambos sentidos; haz clic en el mapa para crear un pedido.",
            wraplength=290,
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(0, 10))

        # Cuadro de Métricas
        frame_metricas = ttk.LabelFrame(panel_izq, text="Estado de la Red", padding=10)
        frame_metricas.pack(fill=tk.X, pady=5)

        self.lbl_nodos = ttk.Label(frame_metricas, text="Nodos: 0", font=("Segoe UI", 9))
        self.lbl_nodos.pack(anchor="w")

        self.lbl_aristas = ttk.Label(frame_metricas, text="Calles transitables: 0", font=("Segoe UI", 9))
        self.lbl_aristas.pack(anchor="w")

        self.lbl_bloqueadas = ttk.Label(
            frame_metricas, text="Calles bloqueadas: 0", font=("Segoe UI", 9, "bold"), foreground="#dc2626"
        )
        self.lbl_bloqueadas.pack(anchor="w")

        self.lbl_ultima_accion = ttk.Label(
            frame_metricas, text="", font=("Segoe UI", 8, "italic"), foreground="#475569"
        )
        self.lbl_ultima_accion.pack(anchor="w")

        # Control interactivo de bloqueo de calles
        frame_bloqueo = ttk.LabelFrame(panel_izq, text="Bloquear / Desbloquear Calle", padding=10)
        frame_bloqueo.pack(fill=tk.X, pady=10)

        nodos_lista = [f"{n.id}: {n.nombre}" for n in self.grafo.nodos.values()]

        ttk.Label(frame_bloqueo, text="Nodo A:").pack(anchor="w", pady=(2, 0))
        self.cb_nodo_a = ttk.Combobox(frame_bloqueo, values=nodos_lista, state="readonly")
        if nodos_lista:
            self.cb_nodo_a.current(0)
        self.cb_nodo_a.pack(fill=tk.X, pady=2)

        ttk.Label(frame_bloqueo, text="Nodo B:").pack(anchor="w", pady=(4, 0))
        self.cb_nodo_b = ttk.Combobox(frame_bloqueo, values=nodos_lista, state="readonly")
        if len(nodos_lista) > 1:
            self.cb_nodo_b.current(1)
        self.cb_nodo_b.pack(fill=tk.X, pady=2)

        btn_toggle = ttk.Button(
            frame_bloqueo,
            text="Alternar Estado de Calle",
            command=self._alternar_calle_desde_combos,
        )
        btn_toggle.pack(fill=tk.X, pady=8)

        btn_restablecer = ttk.Button(
            frame_bloqueo,
            text="Reabrir Todas las Calles",
            command=self._restablecer_calles,
        )
        btn_restablecer.pack(fill=tk.X, pady=2)

        # Configuración de Servidor de Tiles
        frame_tiles = ttk.LabelFrame(panel_izq, text="Capa de Mapa (Tiles)", padding=10)
        frame_tiles.pack(fill=tk.X, pady=10)

        self.var_tiles = tk.StringVar(value="OSM")
        r1 = ttk.Radiobutton(
            frame_tiles,
            text="OpenStreetMap (Estándar)",
            variable=self.var_tiles,
            value="OSM",
            command=self._cambiar_tiles,
        )
        r1.pack(anchor="w", pady=2)

        r2 = ttk.Radiobutton(
            frame_tiles,
            text="Google Maps (Uso Académico)",
            variable=self.var_tiles,
            value="GOOGLE",
            command=self._cambiar_tiles,
        )
        r2.pack(anchor="w", pady=2)

        ttk.Label(
            frame_tiles,
            text="* Google Maps es de uso demostrativo no oficial.",
            font=("Segoe UI", 7, "italic"),
            foreground="#64748b",
            wraplength=270,
        ).pack(anchor="w", pady=(4, 0))

        frame_desvio = ttk.LabelFrame(
            panel_izq, text="Distancia en línea recta vs por calles", padding=5
        )
        frame_desvio.pack(fill=tk.BOTH, expand=True, pady=6)
        columnas = ("arista", "recta", "calles", "factor")
        self.tabla_desvio = ttk.Treeview(
            frame_desvio, columns=columnas, show="headings", height=6
        )
        self.tabla_desvio.heading("arista", text="A -> B")
        self.tabla_desvio.heading("recta", text="Recta m")
        self.tabla_desvio.heading("calles", text="Calles m")
        self.tabla_desvio.heading("factor", text="Factor")
        self.tabla_desvio.column("arista", width=66, anchor="center")
        self.tabla_desvio.column("recta", width=64, anchor="e")
        self.tabla_desvio.column("calles", width=64, anchor="e")
        self.tabla_desvio.column("factor", width=52, anchor="e")
        scroll_desvio = ttk.Scrollbar(
            frame_desvio, orient=tk.VERTICAL, command=self.tabla_desvio.yview
        )
        self.tabla_desvio.configure(yscrollcommand=scroll_desvio.set)
        self.tabla_desvio.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_desvio.pack(side=tk.RIGHT, fill=tk.Y)

        # Panel derecho: Mapa interactivo
        self.componente_mapa = ComponenteMapa(
            self,
            grafo=self.grafo,
            al_hacer_clic_arista=self._al_hacer_clic_calle,
            al_hacer_clic_mapa=self.al_hacer_clic_mapa,
        )
        self.componente_mapa.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Dibujar el grafo inicial
        self.componente_mapa.dibujar_grafo()
        self._cargar_tabla_desvio()

    def _cargar_tabla_desvio(self):
        for arista in self.grafo.todas_las_aristas():
            origen = self.grafo.nodos[arista.origen_id]
            destino = self.grafo.nodos[arista.destino_id]
            recta = distancia_haversine(
                origen.lat, origen.lon, destino.lat, destino.lon
            )
            factor = arista.longitud_m / recta if recta else float("inf")
            self.tabla_desvio.insert(
                "",
                tk.END,
                values=(
                    f"{arista.origen_id}->{arista.destino_id}",
                    f"{recta:.0f}",
                    f"{arista.longitud_m:.0f}",
                    f"{factor:.2f}",
                ),
            )

    def _al_hacer_clic_calle(self, u_id: str, v_id: str):
        """Callback al hacer clic sobre una arista en el mapa."""
        estado_actual = self.grafo.esta_bloqueada(u_id, v_id)
        nuevo_estado = not estado_actual
        # Si estaba bloqueada, activarla (True). Si estaba activa, bloquearla (False)
        self.grafo.cambiar_estado_calle(u_id, v_id, activa=estado_actual)
        self.componente_mapa.dibujar_grafo()
        self.actualizar_estadisticas()
        msg = "cerrada" if nuevo_estado else "reabierta"
        self.lbl_ultima_accion.config(text=f"Calle {u_id} ↔ {v_id} {msg}.")

    def _alternar_calle_desde_combos(self):
        sel_a = self.cb_nodo_a.get()
        sel_b = self.cb_nodo_b.get()
        if not sel_a or not sel_b:
            return
        id_a = sel_a.split(":")[0].strip()
        id_b = sel_b.split(":")[0].strip()

        if id_a == id_b:
            messagebox.showwarning("Atención", "Selecciona dos nodos distintos.")
            return

        # Verificar si existe la arista
        if id_b not in self.grafo.adyacencia.get(id_a, {}):
            messagebox.showinfo(
                "Aviso", f"No existe conexión vial directa entre {id_a} y {id_b}."
            )
            return

        bloqueada = self.grafo.esta_bloqueada(id_a, id_b)
        # Invertir estado
        self.grafo.cambiar_estado_calle(id_a, id_b, activa=bloqueada)
        self.componente_mapa.dibujar_grafo()
        self.actualizar_estadisticas()
        estado = "reabierta" if bloqueada else "cerrada"
        self.lbl_ultima_accion.config(text=f"Calle {id_a} ↔ {id_b} {estado}.")

    def _restablecer_calles(self):
        for arista in self.grafo.todas_las_aristas():
            self.grafo.cambiar_estado_calle(arista.origen_id, arista.destino_id, activa=True)
        self.componente_mapa.dibujar_grafo()
        self.actualizar_estadisticas()
        messagebox.showinfo("Éxito", "Todas las calles han sido reabiertas al tránsito.")

    def _cambiar_tiles(self):
        eleccion = self.var_tiles.get()
        if eleccion == "GOOGLE":
            self.componente_mapa.cambiar_proveedor_tiles(config.TILES_GOOGLE_NORMAL)
        else:
            self.componente_mapa.cambiar_proveedor_tiles(config.TILES_OPENSTREETMAP)

    def refrescar(self):
        """Al volver a la pestaña: refleja calles cerradas desde otras pestañas."""
        if self.componente_mapa.esta_desactualizado():
            self.componente_mapa.dibujar_grafo()
        self.actualizar_estadisticas()

    def actualizar_estadisticas(self):
        n_nodos = len(self.grafo.nodos)
        aristas = self.grafo.todas_las_aristas()
        bloqueadas = sum(1 for a in aristas if not a.activa)
        activas = len(aristas) - bloqueadas

        self.lbl_nodos.config(text=f"Nodos registrados: {n_nodos}")
        self.lbl_aristas.config(text=f"Arcos dirigidos transitables: {activas}")
        self.lbl_bloqueadas.config(text=f"Arcos dirigidos cerrados: {bloqueadas}")
