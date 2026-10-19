"""
Pestaña de Divide y Vencerás (D&C).
Dos modos:
1. Un repartidor por zona (caso del enunciado): la ciudad se divide en R zonas
   espaciales, una por repartidor, y cada uno resuelve la ruta óptima de su zona.
2. Zonas de K pedidos: un solo repartidor recorre zonas de tamaño <= K.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
import config
from core.modelos import Grafo, Pedido, Repartidor
from core.divide_venceras import resolver_rutas_dyv, resolver_por_repartidores
from gui.componente_mapa import ComponenteMapa
from gui.panel_desplazable import crear_panel_lateral

TEORIA_POR_REPARTIDOR = (
    "Partición en R zonas (R = repartidores):\n"
    "  T(n,r) = T(n·⌊r/2⌋/r, ⌊r/2⌋)\n"
    "         + T(n·⌈r/2⌉/r, ⌈r/2⌉) + Θ(n log n)\n"
    "  profundidad ⌈log₂ r⌉ -> Θ(n log n · log r)\n"
    "Ruta por zona: Held-Karp O(k² 2^k), k≈n/r\n"
    "Espacio: O(n)"
)

TEORIA_ZONAS_K = (
    "Partición hasta zonas de ≤ K pedidos:\n"
    "  T(n) = 2T(n/2) + Θ(n log n)  (QuickSort)\n"
    "  Maestro, caso 2 extendido (k=1):\n"
    "  -> Θ(n log² n)\n"
    "Elección voraz de la siguiente zona:\n"
    "  M = n/K zonas -> O(M²·K) = O(n²/K)\n"
    "Total: O(n²/K) | Espacio: O(n)"
)


class TabDyV(ttk.Frame):
    """Pestaña para segmentación espacial por Divide y Vencerás."""

    def __init__(
        self,
        master,
        grafo: Grafo,
        pedidos: List[Pedido],
        repartidores: Optional[List[Repartidor]] = None,
        *args,
        **kwargs,
    ):
        super().__init__(master, *args, **kwargs)
        self.grafo = grafo
        self.pedidos = pedidos
        self.repartidores = repartidores or []

        self._crear_interfaz()

    def _crear_interfaz(self):
        panel_izq = crear_panel_lateral(self, ancho=340, padding=12)

        ttk.Label(
            panel_izq,
            text="Divide y Vencerás (D&C)",
            font=("Segoe UI", 13, "bold"),
            foreground="#1d4ed8",
        ).pack(anchor="w", pady=(0, 4))

        ttk.Label(
            panel_izq,
            text=(
                "Divide la ciudad cortando los pedidos por la mediana, alternando "
                "latitud (norte-sur) y longitud (este-oeste), y resuelve cada zona por separado."
            ),
            wraplength=300,
            font=("Segoe UI", 8),
            foreground="#475569",
        ).pack(anchor="w", pady=(0, 8))

        frame_param = ttk.LabelFrame(panel_izq, text="Modo y parámetros", padding=10)
        frame_param.pack(fill=tk.X, pady=4)

        self.var_modo = tk.StringVar(value="repartidores")
        ttk.Radiobutton(
            frame_param,
            text=f"Una zona por repartidor ({len(self.repartidores)} zonas)",
            variable=self.var_modo,
            value="repartidores",
            command=self._al_cambiar_modo,
        ).pack(anchor="w")
        ttk.Radiobutton(
            frame_param,
            text="Un repartidor, zonas de K pedidos",
            variable=self.var_modo,
            value="k",
            command=self._al_cambiar_modo,
        ).pack(anchor="w", pady=(0, 4))

        self.frame_k = ttk.Frame(frame_param)
        self.frame_k.pack(fill=tk.X)
        ttk.Label(self.frame_k, text="Punto de partida:").pack(anchor="w")
        nodos_lista = [f"{n.id}: {n.nombre}" for n in self.grafo.nodos.values()]
        self.cb_origen = ttk.Combobox(self.frame_k, values=nodos_lista, state="readonly")
        if nodos_lista:
            self.cb_origen.current(0)
        self.cb_origen.pack(fill=tk.X, pady=2)
        ttk.Label(self.frame_k, text="Umbral máx. por zona (K pedidos):").pack(anchor="w", pady=(4, 0))
        self.spin_k = ttk.Spinbox(self.frame_k, from_=2, to=10, width=10)
        self.spin_k.set(str(config.UMBRAL_DYV_K))
        self.spin_k.pack(anchor="w", pady=2)

        self.btn_ejecutar_dyv = ttk.Button(
            frame_param,
            text="Segmentar y optimizar zonas",
            command=self._ejecutar_dyv,
        )
        self.btn_ejecutar_dyv.pack(fill=tk.X, pady=6)

        frame_teoria = ttk.LabelFrame(panel_izq, text="Recurrencia y complejidad", padding=8)
        frame_teoria.pack(fill=tk.X, pady=4)
        self.lbl_teoria = ttk.Label(
            frame_teoria, text=TEORIA_POR_REPARTIDOR, font=("Consolas", 8), foreground="#0f172a",
            justify=tk.LEFT,
        )
        self.lbl_teoria.pack(anchor="w")

        self.frame_res = ttk.LabelFrame(panel_izq, text="Zonas y métricas", padding=8)
        self.frame_res.pack(fill=tk.BOTH, expand=True, pady=4)
        self.txt_zonas = tk.Text(self.frame_res, height=9, width=38, font=("Consolas", 8))
        self.txt_zonas.pack(fill=tk.BOTH, expand=True)

        self.componente_mapa = ComponenteMapa(self, grafo=self.grafo)
        self.componente_mapa.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.componente_mapa.dibujar_grafo()
        self._al_cambiar_modo()

    def _al_cambiar_modo(self):
        modo_k = self.var_modo.get() == "k"
        for w in self.frame_k.winfo_children():
            try:
                w.configure(state=("readonly" if isinstance(w, ttk.Combobox) else "normal") if modo_k else "disabled")
            except tk.TclError:
                pass
        self.lbl_teoria.config(text=TEORIA_ZONAS_K if modo_k else TEORIA_POR_REPARTIDOR)

    def refrescar(self):
        if self.componente_mapa.esta_desactualizado():
            self.componente_mapa.dibujar_grafo()

    def _ejecutar_dyv(self):
        if not self.pedidos:
            messagebox.showinfo("Atención", "No hay pedidos registrados.")
            return
        try:
            if self.var_modo.get() == "repartidores":
                self._ejecutar_por_repartidores()
            else:
                self._ejecutar_zonas_k()
        except ValueError as error:
            messagebox.showerror("Ruta no disponible", str(error))

    def _ejecutar_por_repartidores(self):
        if not self.repartidores:
            messagebox.showinfo("Atención", "No hay repartidores cargados.")
            return
        zonas = resolver_por_repartidores(self.pedidos, self.repartidores, self.grafo)
        nombres = {r.id: r for r in self.repartidores}

        self.componente_mapa.dibujar_grafo()
        t = self.txt_zonas
        t.delete("1.0", tk.END)
        t.insert(tk.END, "=== UNA ZONA POR REPARTIDOR ===\n")
        total = 0.0
        mas_larga = 0.0
        for idx, z in enumerate(zonas):
            color = config.COLORES_ZONAS[idx % len(config.COLORES_ZONAS)]
            rep = nombres.get(z.repartidor_id)
            for p in z.pedidos:
                self.componente_mapa.agregar_marcador_pedido(
                    p.lat, p.lon, f"Z{z.id_zona}", color=color
                )
            if z.ruta_local and len(z.ruta_local.secuencia_nodos) > 1:
                self.componente_mapa.resaltar_ruta(
                    z.ruta_local.secuencia_nodos, color=color, ancho=5,
                    nombre_ruta=f"Zona {z.id_zona}",
                )
            dist = z.ruta_local.distancia_total_m if z.ruta_local else 0.0
            total += dist
            mas_larga = max(mas_larga, dist)
            t.insert(
                tk.END,
                f"\nZona {z.id_zona} -> {rep.nombre if rep else '-'}\n"
                f"  {len(z.pedidos)} pedidos | {dist:,.1f} m\n"
                f"  Método: {z.ruta_local.algoritmo_utilizado if z.ruta_local else '-'}\n",
            )
        t.insert(tk.END, f"\nDistancia total del equipo: {total:,.1f} m\n")
        t.insert(tk.END, f"Ruta más larga (fin del reparto): {mas_larga:,.1f} m\n")

    def _ejecutar_zonas_k(self):
        origen_id = self.cb_origen.get().split(":")[0].strip()
        try:
            k = int(self.spin_k.get())
        except ValueError:
            k = config.UMBRAL_DYV_K
        if k < 1:
            messagebox.showerror("Error", "K debe ser al menos 1.")
            return

        zonas, ruta_global = resolver_rutas_dyv(
            nodo_inicio_id=origen_id, pedidos=self.pedidos, grafo=self.grafo, umbral_k=k
        )

        self.componente_mapa.dibujar_grafo()
        for idx, z in enumerate(zonas):
            color_zona = config.COLORES_ZONAS[idx % len(config.COLORES_ZONAS)]
            for p in z.pedidos:
                self.componente_mapa.agregar_marcador_pedido(
                    p.lat, p.lon, f"Z{idx + 1}", color=color_zona
                )
        self.componente_mapa.resaltar_ruta(
            ruta_global.secuencia_nodos, color="#2563eb", ancho=5, nombre_ruta="Ruta combinada D&C"
        )

        t = self.txt_zonas
        t.delete("1.0", tk.END)
        t.insert(tk.END, "=== ZONAS DE K PEDIDOS ===\n")
        t.insert(tk.END, f"Zonas generadas: {len(zonas)} (K ≤ {k})\n")
        t.insert(tk.END, f"Distancia total por calles: {ruta_global.distancia_total_m:,.2f} m\n")
        t.insert(tk.END, f"Tiempo: {ruta_global.tiempo_computo_ms:.3f} ms\n")
        t.insert(tk.END, "Orden de visita de zonas:\n")
        for idx, zona in enumerate(zonas):
            dist_loc = zona.ruta_local.distancia_total_m if zona.ruta_local else 0
            t.insert(
                tk.END,
                f"  Z{idx + 1}: {len(zona.pedidos)} pedidos | {dist_loc:,.1f} m\n",
            )
