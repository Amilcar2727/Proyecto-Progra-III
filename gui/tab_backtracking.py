"""
Pestaña de Backtracking con Poda (Búsqueda Exhaustiva Inteligente).
Encuentra todas las rutas simples entre origen y destino evitando calles cerradas,
aplica poda por costo acumulado Branch & Bound, y permite inspeccionar rutas en el mapa.
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Tuple
import config
from core.modelos import Grafo
from core.backtracking import buscar_rutas_backtracking, ResultadoBacktracking
from gui.componente_mapa import ComponenteMapa


class TabBacktracking(ttk.Frame):
    """Pestaña para cálculo exhaustivo de rutas con poda y manejo de calles bloqueadas."""

    def __init__(self, master, grafo: Grafo, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.grafo = grafo
        self.rutas_actuales: List[Tuple[List[str], float]] = []

        self._crear_interfaz()

    def _crear_interfaz(self):
        panel_izq = ttk.Frame(self, width=350, padding=10)
        panel_izq.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(
            panel_izq,
            text="Backtracking con Poda",
            font=("Segoe UI", 13, "bold"),
            foreground="#b45309",
        ).pack(anchor="w", pady=(0, 4))

        ttk.Label(
            panel_izq,
            text="Exploración DFS de caminos simples. Poda ramas cuando el costo acumulado supera a la mejor distancia encontrada.",
            wraplength=310,
            font=("Segoe UI", 8),
            foreground="#475569",
        ).pack(anchor="w", pady=(0, 8))

        # Panel de Selección de Nodos
        frame_sel = ttk.LabelFrame(panel_izq, text="Puntos de Ruta", padding=8)
        frame_sel.pack(fill=tk.X, pady=4)

        nodos_lista = [f"{n.id}: {n.nombre}" for n in self.grafo.nodos.values()]

        ttk.Label(frame_sel, text="Nodo Origen:").pack(anchor="w")
        self.cb_origen = ttk.Combobox(frame_sel, values=nodos_lista, state="readonly")
        if len(nodos_lista) > 1:
            self.cb_origen.current(1)  # N02: San Blas
        self.cb_origen.pack(fill=tk.X, pady=2)

        ttk.Label(frame_sel, text="Nodo Destino:").pack(anchor="w", pady=(4, 0))
        self.cb_destino = ttk.Combobox(frame_sel, values=nodos_lista, state="readonly")
        if len(nodos_lista) > 10:
            self.cb_destino.current(10)  # N11: Wanchaq
        self.cb_destino.pack(fill=tk.X, pady=2)

        self.btn_buscar_rutas = ttk.Button(
            frame_sel,
            text="Explorar Todas las Rutas Simples",
            command=self._lanzar_hilo_backtracking,
        )
        self.btn_buscar_rutas.pack(fill=tk.X, pady=6)

        self.progreso_bt = ttk.Progressbar(frame_sel, mode="indeterminate")
        self.progreso_bt.pack(fill=tk.X, pady=2)

        # Estadísticas de Poda
        self.frame_metricas = ttk.LabelFrame(panel_izq, text="Métricas del Árbol de Estados", padding=8)
        self.frame_metricas.pack(fill=tk.X, pady=4)

        self.lbl_rutas_totales = ttk.Label(self.frame_metricas, text="Rutas viables encontradas: 0", font=("Segoe UI", 8))
        self.lbl_rutas_totales.pack(anchor="w")

        self.lbl_podas = ttk.Label(self.frame_metricas, text="Ramas podadas por cota: 0", font=("Segoe UI", 8, "bold"), foreground="#047857")
        self.lbl_podas.pack(anchor="w")

        self.lbl_estados = ttk.Label(self.frame_metricas, text="Estados visitados: 0", font=("Segoe UI", 8))
        self.lbl_estados.pack(anchor="w")

        self.lbl_tiempo = ttk.Label(self.frame_metricas, text="Tiempo de cómputo: 0.0 ms", font=("Segoe UI", 8))
        self.lbl_tiempo.pack(anchor="w")

        # Bloquear/Desbloquear calle interactiva
        frame_calle = ttk.LabelFrame(panel_izq, text="Gestión de Calles Cerradas", padding=6)
        frame_calle.pack(fill=tk.X, pady=4)

        ttk.Label(frame_calle, text="Haz clic sobre una calle en el mapa o usa los combos para cerrarla/reabrirla.", wraplength=300, font=("Segoe UI", 7, "italic")).pack(anchor="w")

        # Lista de Rutas Encontradas
        frame_lista = ttk.LabelFrame(panel_izq, text="Rutas Encontradas (Clic para inspeccionar)", padding=6)
        frame_lista.pack(fill=tk.BOTH, expand=True, pady=4)

        self.lista_rutas = tk.Listbox(frame_lista, font=("Consolas", 8), height=6)
        self.lista_rutas.bind("<<ListboxSelect>>", self._al_seleccionar_ruta_lista)
        self.lista_rutas.pack(fill=tk.BOTH, expand=True)

        # Mapa a la derecha
        self.componente_mapa = ComponenteMapa(
            self,
            grafo=self.grafo,
            al_hacer_clic_arista=self._al_hacer_clic_calle,
        )
        self.componente_mapa.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.componente_mapa.dibujar_grafo()

    def _al_hacer_clic_calle(self, u_id: str, v_id: str):
        estado_actual = self.grafo.esta_bloqueada(u_id, v_id)
        self.grafo.cambiar_estado_calle(u_id, v_id, activa=estado_actual)
        self.componente_mapa.dibujar_grafo()
        # Si ya había rutas calculadas, recalcular automáticamente
        self._lanzar_hilo_backtracking()

    def _lanzar_hilo_backtracking(self):
        sel_orig = self.cb_origen.get()
        sel_dest = self.cb_destino.get()
        if not sel_orig or not sel_dest:
            return

        u = sel_orig.split(":")[0].strip()
        v = sel_dest.split(":")[0].strip()

        if u == v:
            messagebox.showwarning("Atención", "El origen y destino deben ser nodos distintos.")
            return

        self.btn_buscar_rutas.config(state="disabled")
        self.progreso_bt.start(10)

        hilo = threading.Thread(target=self._hilo_backtracking, args=(u, v), daemon=True)
        hilo.start()

    def _hilo_backtracking(self, origen_id: str, destino_id: str):
        resultado = buscar_rutas_backtracking(
            grafo=self.grafo,
            origen_id=origen_id,
            destino_id=destino_id,
            max_rutas=config.LIMITE_BACKTRACKING_RUTAS,
            timeout_seg=config.TIMEOUT_BACKTRACKING_SEG,
        )
        self.after(0, self._finalizar_backtracking, resultado)

    def _finalizar_backtracking(self, resultado: ResultadoBacktracking):
        self.progreso_bt.stop()
        self.btn_buscar_rutas.config(state="normal")

        self.rutas_actuales = resultado.rutas_encontradas

        self.lbl_rutas_totales.config(text=f"Rutas viables encontradas: {len(self.rutas_actuales)}")
        self.lbl_podas.config(text=f"Ramas podadas por cota: {resultado.total_ramas_podadas}")
        self.lbl_estados.config(text=f"Estados visitados: {resultado.total_estados_visitados}")
        self.lbl_tiempo.config(text=f"Tiempo de cómputo: {resultado.tiempo_computo_ms:.3f} ms")

        # Cargar lista
        self.lista_rutas.delete(0, tk.END)
        for idx, (camino, dist) in enumerate(self.rutas_actuales):
            etiqueta = f"#{idx + 1} [{dist:,.1f}m] {' -> '.join(camino)}"
            if idx == 0:
                etiqueta = "★ [ÓPTIMA] " + etiqueta
            self.lista_rutas.insert(tk.END, etiqueta)

        # Dibujar en mapa
        self.componente_mapa.dibujar_grafo()

        if resultado.ruta_optima:
            camino_opt, dist_opt = resultado.ruta_optima
            self.componente_mapa.resaltar_ruta(
                camino_opt,
                color=config.COLOR_RUTA_OPTIMA,
                ancho=5,
                nombre_ruta="Ruta Óptima Backtracking",
            )
            # Seleccionar la primera en la lista
            self.lista_rutas.select_set(0)
        else:
            messagebox.showinfo("Sin Conexión", "No existen rutas viables con las calles actualmente transitables.")

    def _al_seleccionar_ruta_lista(self, event):
        sel = self.lista_rutas.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx < len(self.rutas_actuales):
            camino, dist = self.rutas_actuales[idx]
            self.componente_mapa.dibujar_grafo()
            color = config.COLOR_RUTA_OPTIMA if idx == 0 else config.COLOR_RUTA_BACKTRACKING
            self.componente_mapa.resaltar_ruta(
                camino,
                color=color,
                ancho=5,
                nombre_ruta=f"Ruta #{idx + 1}",
            )
