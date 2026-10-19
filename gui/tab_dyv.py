"""
Pestaña de Divide y Vencerás (D&C).
Segmentación recursiva espacial en cuadrantes/zonas por mediana alternada de lat/lon,
resolución local de sub-rutas, ensamble y coloreado por clústeres en el mapa.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List
import config
from core.modelos import Grafo, Pedido
from core.divide_venceras import resolver_rutas_dyv
from gui.componente_mapa import ComponenteMapa


class TabDyV(ttk.Frame):
    """Pestaña para segmentación espacial por Divide y Vencerás."""

    def __init__(self, master, grafo: Grafo, pedidos: List[Pedido], *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.grafo = grafo
        self.pedidos = pedidos

        self._crear_interfaz()

    def _crear_interfaz(self):
        panel_izq = ttk.Frame(self, width=340, padding=12)
        panel_izq.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(
            panel_izq,
            text="Divide y Vencerás (D&C)",
            font=("Segoe UI", 13, "bold"),
            foreground="#1d4ed8",
        ).pack(anchor="w", pady=(0, 4))

        ttk.Label(
            panel_izq,
            text="Descompone el conjunto de pedidos en cuadrantes balanceados por mediana espacial (alternando lat/lon) hasta hojas de tamaño ≤ K.",
            wraplength=300,
            font=("Segoe UI", 8),
            foreground="#475569",
        ).pack(anchor="w", pady=(0, 8))

        frame_param = ttk.LabelFrame(panel_izq, text="Parámetros de Partición", padding=10)
        frame_param.pack(fill=tk.X, pady=4)

        ttk.Label(frame_param, text="Punto de Partida:").pack(anchor="w")
        nodos_lista = [f"{n.id}: {n.nombre}" for n in self.grafo.nodos.values()]
        self.cb_origen = ttk.Combobox(frame_param, values=nodos_lista, state="readonly")
        if nodos_lista:
            self.cb_origen.current(0)
        self.cb_origen.pack(fill=tk.X, pady=2)

        ttk.Label(frame_param, text="Umbral máx. por zona (K pedidos):").pack(anchor="w", pady=(4, 0))
        self.spin_k = ttk.Spinbox(frame_param, from_=2, to=10, width=10)
        self.spin_k.set("5")
        self.spin_k.pack(anchor="w", pady=2)

        self.btn_ejecutar_dyv = ttk.Button(
            frame_param,
            text="Segmentar y Optimizar Zonas",
            command=self._ejecutar_dyv,
        )
        self.btn_ejecutar_dyv.pack(fill=tk.X, pady=6)

        # Análisis Teórico (Teorema Maestro)
        frame_teoria = ttk.LabelFrame(panel_izq, text="Ecuación de Recurrencia", padding=8)
        frame_teoria.pack(fill=tk.X, pady=4)

        texto_teoria = (
            "Recurrencia de Partición:\n"
            "  T(n) = 2 T(n/2) + O(n)\n"
            "Teorema Maestro (Caso 2):\n"
            "  a=2, b=2, f(n)=O(n)\n"
            "  n^(log_2 2) = n^1 = n\n"
            "  f(n) = Theta(n) => T(n) = O(n log n)\n"
            "Espacio: O(n) auxiliar"
        )
        lbl_teoria = ttk.Label(
            frame_teoria,
            text=texto_teoria,
            font=("Consolas", 8),
            foreground="#0f172a",
        )
        lbl_teoria.pack(anchor="w")

        # Resultados
        self.frame_res = ttk.LabelFrame(panel_izq, text="Zonas y Métricas", padding=8)
        self.frame_res.pack(fill=tk.BOTH, expand=True, pady=4)

        self.txt_zonas = tk.Text(self.frame_res, height=9, width=35, font=("Consolas", 8))
        self.txt_zonas.pack(fill=tk.BOTH, expand=True)

        # Mapa interactivo a la derecha
        self.componente_mapa = ComponenteMapa(self, grafo=self.grafo)
        self.componente_mapa.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.componente_mapa.dibujar_grafo()

    def _ejecutar_dyv(self):
        sel_origen = self.cb_origen.get()
        if not sel_origen:
            return
        origen_id = sel_origen.split(":")[0].strip()

        try:
            k = int(self.spin_k.get())
        except ValueError:
            k = 5

        try:
            zonas, ruta_global = resolver_rutas_dyv(
                nodo_inicio_id=origen_id,
                pedidos=self.pedidos,
                grafo=self.grafo,
                umbral_k=k,
            )
        except ValueError as error:
            messagebox.showerror("Ruta no disponible", str(error))
            return

        # Dibujar en mapa
        self.componente_mapa.dibujar_grafo()

        # Resaltar pedidos por color de zona
        for idx, z in enumerate(zonas):
            color_zona = config.COLORES_ZONAS[idx % len(config.COLORES_ZONAS)]
            for p in z.pedidos:
                self.componente_mapa.agregar_marcador_pedido(
                    p.lat, p.lon, f"Z{z.id_zona}: {p.id}", color=color_zona
                )

        # Trazar la ruta combinada global
        self.componente_mapa.resaltar_ruta(
            ruta_global.secuencia_nodos,
            color="#2563eb",
            ancho=5,
            nombre_ruta="Ruta Combinada DyV",
        )

        # Mostrar métricas
        self.txt_zonas.delete("1.0", tk.END)
        self.txt_zonas.insert(tk.END, "=== RESULTADOS DIVIDE & VENCERÁS ===\n")
        self.txt_zonas.insert(tk.END, f"Zonas generadas: {len(zonas)} (K ≤ {k})\n")
        self.txt_zonas.insert(tk.END, f"Distancia total por calles: {ruta_global.distancia_total_m:,.2f} m\n")
        self.txt_zonas.insert(tk.END, f"Tiempo de partición y ensamble: {ruta_global.tiempo_computo_ms:.3f} ms\n\n")

        for z in enumerate(zonas):
            idx, zona = z
            dist_loc = zona.ruta_local.distancia_total_m if zona.ruta_local else 0
            self.txt_zonas.insert(
                tk.END,
                f"Zona {zona.id_zona}: {len(zona.pedidos)} pedidos | Sub-dist: {dist_loc:,.1f} m\n",
            )
