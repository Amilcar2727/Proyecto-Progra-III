"""
Pestaña de Paradigma Voraz (Greedy).
Implementa Vecino Más Cercano (TSP) y Asignación de Pedidos de Emergencia
con trazado de rutas sobre el mapa y reporte de métricas en tiempo real.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List
import config
from core.modelos import Grafo, Pedido, Repartidor
from core.greedy import vecino_mas_cercano, asignar_pedido_emergencia
from gui.componente_mapa import ComponenteMapa


class TabGreedy(ttk.Frame):
    """Pestaña para experimentación con algoritmos Greedy."""

    def __init__(
        self,
        master,
        grafo: Grafo,
        pedidos: List[Pedido],
        repartidores: List[Repartidor],
        *args,
        **kwargs,
    ):
        super().__init__(master, *args, **kwargs)
        self.grafo = grafo
        self.pedidos = pedidos
        self.repartidores = repartidores

        self._crear_interfaz()

    def _crear_interfaz(self):
        panel_izq = ttk.Frame(self, width=340, padding=12)
        panel_izq.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(
            panel_izq,
            text="Algoritmos Voraces (Greedy)",
            font=("Segoe UI", 13, "bold"),
            foreground="#065f46",
        ).pack(anchor="w", pady=(0, 4))

        ttk.Label(
            panel_izq,
            text="Toma la mejor decisión local inmediata por distancia dirigida de red en cada paso, sin reconsiderar el pasado.",
            wraplength=300,
            font=("Segoe UI", 8),
            foreground="#475569",
        ).pack(anchor="w", pady=(0, 8))

        # Sección 1: Vecino más cercano
        frame_tsp = ttk.LabelFrame(panel_izq, text="1. Ruta Voraz (Vecino Cercano)", padding=10)
        frame_tsp.pack(fill=tk.X, pady=4)

        ttk.Label(frame_tsp, text="Punto de Partida del Repartidor:").pack(anchor="w")
        nodos_lista = [f"{n.id}: {n.nombre}" for n in self.grafo.nodos.values()]
        self.cb_origen = ttk.Combobox(frame_tsp, values=nodos_lista, state="readonly")
        if nodos_lista:
            self.cb_origen.current(0)  # Plaza de Armas
        self.cb_origen.pack(fill=tk.X, pady=2)

        ttk.Label(frame_tsp, text="Cantidad de Pedidos a Entregar (N):").pack(anchor="w", pady=(4, 0))
        self.spin_n = ttk.Spinbox(frame_tsp, from_=3, to=len(self.pedidos), width=10)
        self.spin_n.set("8")
        self.spin_n.pack(anchor="w", pady=2)

        self.var_retorno = tk.BooleanVar(value=False)
        chk_ret = ttk.Checkbutton(frame_tsp, text="Retornar al punto inicial", variable=self.var_retorno)
        chk_ret.pack(anchor="w", pady=2)

        self.btn_ejecutar_tsp = ttk.Button(
            frame_tsp,
            text="Calcular Ruta Voraz O(n²)",
            command=self._ejecutar_vecino_cercano,
        )
        self.btn_ejecutar_tsp.pack(fill=tk.X, pady=6)

        # Sección 2: Asignación de Emergencia
        frame_emergencia = ttk.LabelFrame(panel_izq, text="2. Despacho de Emergencia", padding=10)
        frame_emergencia.pack(fill=tk.X, pady=6)

        ttk.Label(frame_emergencia, text="Seleccionar Pedido Crítico:").pack(anchor="w")
        pedidos_urgentes = [f"{p.id} | {p.cliente} ({p.sector})" for p in self.pedidos if p.prioridad == 1]
        self.cb_emergencia = ttk.Combobox(
            frame_emergencia,
            values=pedidos_urgentes or [f"{p.id} | {p.cliente}" for p in self.pedidos[:6]],
            state="readonly",
        )
        if self.cb_emergencia["values"]:
            self.cb_emergencia.current(0)
        self.cb_emergencia.pack(fill=tk.X, pady=2)

        self.btn_asignar = ttk.Button(
            frame_emergencia,
            text="Asignar al Repartidor Más Próximo O(R)",
            command=self._ejecutar_asignacion_emergencia,
        )
        self.btn_asignar.pack(fill=tk.X, pady=6)

        # Métricas de salida
        self.frame_resultados = ttk.LabelFrame(panel_izq, text="Métricas del Algoritmo", padding=8)
        self.frame_resultados.pack(fill=tk.BOTH, expand=True, pady=4)

        self.txt_resultados = tk.Text(self.frame_resultados, height=9, width=35, font=("Consolas", 8))
        self.txt_resultados.pack(fill=tk.BOTH, expand=True)

        # Mapa interactivo a la derecha
        self.componente_mapa = ComponenteMapa(self, grafo=self.grafo)
        self.componente_mapa.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.componente_mapa.dibujar_grafo()

    def _ejecutar_vecino_cercano(self):
        sel_origen = self.cb_origen.get()
        if not sel_origen:
            return
        origen_id = sel_origen.split(":")[0].strip()

        try:
            n_pedidos = int(self.spin_n.get())
        except ValueError:
            n_pedidos = 8

        sub_pedidos = self.pedidos[:n_pedidos]
        try:
            ruta = vecino_mas_cercano(
                nodo_inicio_id=origen_id,
                pedidos=sub_pedidos,
                grafo=self.grafo,
                retornar_al_inicio=self.var_retorno.get(),
            )
        except ValueError as error:
            messagebox.showerror("Ruta no disponible", str(error))
            return

        # Dibujar en mapa
        self.componente_mapa.dibujar_grafo()
        self.componente_mapa.resaltar_ruta(
            ruta.secuencia_nodos,
            color=config.COLOR_RUTA_GREEDY,
            ancho=5,
            nombre_ruta="Ruta Greedy",
        )

        # Mostrar métricas
        self.txt_resultados.delete("1.0", tk.END)
        self.txt_resultados.insert(tk.END, "=== RESULTADOS GREEDY (TSP) ===\n")
        self.txt_resultados.insert(tk.END, f"Algoritmo: {ruta.algoritmo_utilizado}\n")
        self.txt_resultados.insert(tk.END, f"Complejidad: O(n²) tiempo, O(n) espacio\n")
        self.txt_resultados.insert(tk.END, f"Distancia total por calles: {ruta.distancia_total_m:,.2f} m\n")
        self.txt_resultados.insert(tk.END, f"Tiempo de cómputo: {ruta.tiempo_computo_ms:.3f} ms\n")
        self.txt_resultados.insert(tk.END, f"Paradas: {len(ruta.secuencia_nodos)} nodos\n")
        self.txt_resultados.insert(tk.END, f"Secuencia: {' -> '.join(ruta.secuencia_nodos)}\n")

    def _ejecutar_asignacion_emergencia(self):
        sel = self.cb_emergencia.get()
        if not sel:
            return
        pid = sel.split("|")[0].strip()

        pedido_urgente = next((p for p in self.pedidos if p.id == pid), None)
        if not pedido_urgente:
            return

        repartidor, dist, t_ms = asignar_pedido_emergencia(
            pedido_urgente, self.repartidores, self.grafo
        )

        self.txt_resultados.delete("1.0", tk.END)
        self.txt_resultados.insert(tk.END, "=== ASIGNACIÓN DE EMERGENCIA ===\n")
        if repartidor:
            self.txt_resultados.insert(tk.END, f"Pedido: {pedido_urgente.id} (Urgente)\n")
            self.txt_resultados.insert(tk.END, f"Repartidor Asignado: {repartidor.nombre}\n")
            self.txt_resultados.insert(tk.END, f"Vehículo: {repartidor.tipo_vehiculo}\n")
            self.txt_resultados.insert(tk.END, f"Distancia por calles: {dist:,.2f} m\n")
            self.txt_resultados.insert(tk.END, f"Tiempo de decisión: {t_ms:.3f} ms\n")
            self.txt_resultados.insert(tk.END, f"Complejidad: O(R) = O(3) -> O(1)\n")

            # Resaltar en mapa
            self.componente_mapa.dibujar_grafo()
            nodo_rep_id = repartidor.nodo_actual_id or repartidor.nodo_inicio_id
            self.componente_mapa.resaltar_ruta(
                [nodo_rep_id, pedido_urgente.nodo_id],
                color="#e11d48",
                ancho=4,
                nombre_ruta="Despacho de emergencia",
            )
        else:
            self.txt_resultados.insert(
                tk.END,
                "No hay repartidor con capacidad disponible y un camino transitable hasta el pedido.\n",
            )
