"""
Pestaña de Programación Dinámica (PD).
Implementa Mochila 0/1 (Knapsack) con visualización de la matriz DP y reconstrucción,
y Held-Karp (TSP Óptimo con Bitmask y Memoización) comparado contra Greedy
ejecutado en un hilo de fondo (threading) para no congelar la GUI.
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Tuple
import config
from core.modelos import Grafo, Pedido
from core.prog_dinamica import resolver_mochila_01, held_karp_tsp
from core.greedy import vecino_mas_cercano
from gui.componente_mapa import ComponenteMapa


class TabPD(ttk.Frame):
    """Pestaña que contiene Mochila 0/1 y Held-Karp."""

    def __init__(self, master, grafo: Grafo, pedidos: List[Pedido], *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.grafo = grafo
        self.pedidos = pedidos

        self._crear_interfaz()

    def _crear_interfaz(self):
        nb_pd = ttk.Notebook(self)
        nb_pd.pack(fill=tk.BOTH, expand=True)

        self.tab_mochila = ttk.Frame(nb_pd, padding=8)
        self.tab_held_karp = ttk.Frame(nb_pd, padding=8)

        nb_pd.add(self.tab_mochila, text="  1. Mochila 0/1 (Carga Óptima)  ")
        nb_pd.add(self.tab_held_karp, text="  2. Held-Karp (TSP Exacto O(n² 2ⁿ))  ")

        self._configurar_subtab_mochila()
        self._configurar_subtab_held_karp()

    def _configurar_subtab_mochila(self):
        panel_izq = ttk.Frame(self.tab_mochila, width=340, padding=10)
        panel_izq.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(
            panel_izq,
            text="Mochila 0/1 (Knapsack)",
            font=("Segoe UI", 13, "bold"),
            foreground="#6b21a8",
        ).pack(anchor="w", pady=(0, 4))

        ttk.Label(
            panel_izq,
            text="Maximiza el valor económico total transportado sin exceder la capacidad de peso del repartidor. Paradigma: Subestructura Óptima.",
            wraplength=300,
            font=("Segoe UI", 8),
            foreground="#475569",
        ).pack(anchor="w", pady=(0, 8))

        frame_cap = ttk.LabelFrame(panel_izq, text="Capacidad del Repartidor", padding=10)
        frame_cap.pack(fill=tk.X, pady=4)

        ttk.Label(frame_cap, text="Capacidad de Carga Máxima (kg):").pack(anchor="w")
        self.spin_peso_max = ttk.Spinbox(frame_cap, from_=5, to=50, width=10)
        self.spin_peso_max.set("25")
        self.spin_peso_max.pack(anchor="w", pady=3)

        ttk.Label(frame_cap, text="Subconjunto de Pedidos a Evaluar (N):").pack(anchor="w", pady=(4, 0))
        self.spin_n_mochila = ttk.Spinbox(frame_cap, from_=5, to=len(self.pedidos), width=10)
        self.spin_n_mochila.set("15")
        self.spin_n_mochila.pack(anchor="w", pady=3)

        self.btn_resolver_mochila = ttk.Button(
            frame_cap,
            text="Calcular Solución Óptima (PD)",
            command=self._ejecutar_mochila,
        )
        self.btn_resolver_mochila.pack(fill=tk.X, pady=8)

        self.frame_res_mochila = ttk.LabelFrame(panel_izq, text="Resumen de Carga Óptima", padding=8)
        self.frame_res_mochila.pack(fill=tk.BOTH, expand=True, pady=4)

        self.txt_res_mochila = tk.Text(self.frame_res_mochila, height=10, width=35, font=("Consolas", 8))
        self.txt_res_mochila.pack(fill=tk.BOTH, expand=True)

        # Panel derecho: Matriz DP
        panel_der = ttk.LabelFrame(self.tab_mochila, text="Matriz de Programación Dinámica DP[i][w] (Inspección Académica)", padding=8)
        panel_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.lbl_info_matriz = ttk.Label(
            panel_der,
            text="Filas: Ítems considerados (i) | Columnas: Capacidad parcial en kg (w)",
            font=("Segoe UI", 8, "italic"),
            foreground="#64748b",
        )
        self.lbl_info_matriz.pack(anchor="w", pady=(0, 4))

        frame_tabla_scroll = ttk.Frame(panel_der)
        frame_tabla_scroll.pack(fill=tk.BOTH, expand=True)

        self.tabla_dp = ttk.Treeview(frame_tabla_scroll, show="headings", height=15)
        scroll_x = ttk.Scrollbar(frame_tabla_scroll, orient=tk.HORIZONTAL, command=self.tabla_dp.xview)
        scroll_y = ttk.Scrollbar(frame_tabla_scroll, orient=tk.VERTICAL, command=self.tabla_dp.yview)
        self.tabla_dp.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)

        self.tabla_dp.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

    def _configurar_subtab_held_karp(self):
        panel_izq = ttk.Frame(self.tab_held_karp, width=340, padding=10)
        panel_izq.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(
            panel_izq,
            text="Held-Karp (TSP Exacto)",
            font=("Segoe UI", 13, "bold"),
            foreground="#4338ca",
        ).pack(anchor="w", pady=(0, 4))

        ttk.Label(
            panel_izq,
            text="Encuentra la ruta EXACTA de costo mínimo usando Programación Dinámica con máscara de bits (Bitmask). Complejidad: O(n² 2ⁿ).",
            wraplength=300,
            font=("Segoe UI", 8),
            foreground="#475569",
        ).pack(anchor="w", pady=(0, 8))

        frame_hk = ttk.LabelFrame(panel_izq, text="Configuración TSP", padding=10)
        frame_hk.pack(fill=tk.X, pady=4)

        ttk.Label(frame_hk, text="Cantidad de Puntos N (Límite Seguro ≤ 12):").pack(anchor="w")
        self.spin_n_hk = ttk.Spinbox(frame_hk, from_=3, to=14, width=10)
        self.spin_n_hk.set("8")
        self.spin_n_hk.pack(anchor="w", pady=3)

        self.btn_ejecutar_hk = ttk.Button(
            frame_hk,
            text="Ejecutar Held-Karp vs Greedy",
            command=self._lanzar_hilo_held_karp,
        )
        self.btn_ejecutar_hk.pack(fill=tk.X, pady=8)

        self.progreso_hk = ttk.Progressbar(frame_hk, mode="indeterminate")
        self.progreso_hk.pack(fill=tk.X, pady=2)

        self.frame_res_hk = ttk.LabelFrame(panel_izq, text="Comparativa de Rendimiento", padding=8)
        self.frame_res_hk.pack(fill=tk.BOTH, expand=True, pady=4)

        self.txt_res_hk = tk.Text(self.frame_res_hk, height=11, width=35, font=("Consolas", 8))
        self.txt_res_hk.pack(fill=tk.BOTH, expand=True)

        # Mapa a la derecha
        self.mapa_hk = ComponenteMapa(self.tab_held_karp, grafo=self.grafo)
        self.mapa_hk.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.mapa_hk.dibujar_grafo()

    def _ejecutar_mochila(self):
        try:
            w_max = int(self.spin_peso_max.get())
            n_items = int(self.spin_n_mochila.get())
        except ValueError:
            messagebox.showerror("Error", "Parámetros numéricos inválidos.")
            return

        candidatos = self.pedidos[:n_items]
        valor_opt, seleccionados, dp = resolver_mochila_01(candidatos, w_max)

        peso_total = sum(p.peso_kg for p in seleccionados)
        vol_total = sum(p.volumen_l for p in seleccionados)

        # Mostrar resumen
        self.txt_res_mochila.delete("1.0", tk.END)
        self.txt_res_mochila.insert(tk.END, "=== MOCHILA 0/1 (PD) ===\n")
        self.txt_res_mochila.insert(tk.END, f"Valor Máximo: S/. {valor_opt:,.2f}\n")
        self.txt_res_mochila.insert(tk.END, f"Capacidad límite: {w_max} kg\n")
        self.txt_res_mochila.insert(tk.END, f"Peso acumulado: {peso_total:.1f} kg\n")
        self.txt_res_mochila.insert(tk.END, f"Volumen total: {vol_total:.1f} L\n")
        self.txt_res_mochila.insert(tk.END, f"Pedidos elegidos: {len(seleccionados)}/{len(candidatos)}\n\n")
        for p in seleccionados:
            self.txt_res_mochila.insert(tk.END, f"• {p.id}: {p.peso_kg:.1f}kg -> S/. {p.valor_soles:.1f}\n")

        # Cargar matriz DP en Treeview
        for item in self.tabla_dp.get_children():
            self.tabla_dp.delete(item)

        cols = ["Item / w"] + [f"{w}kg" for w in range(w_max + 1)]
        self.tabla_dp["columns"] = cols
        for c in cols:
            self.tabla_dp.heading(c, text=c)
            self.tabla_dp.column(c, width=55, anchor="center")

        # Fila 0 (Caso base)
        self.tabla_dp.insert("", tk.END, values=["i=0 (Base)"] + [f"{v:.0f}" for v in dp[0]])

        # Filas 1..N
        for i in range(1, len(dp)):
            p = candidatos[i - 1]
            etiqueta = f"i={i} ({p.id})"
            fila_vals = [etiqueta] + [f"{v:.0f}" for v in dp[i]]
            self.tabla_dp.insert("", tk.END, values=fila_vals)

    def _lanzar_hilo_held_karp(self):
        try:
            n = int(self.spin_n_hk.get())
        except ValueError:
            n = 8

        if n > config.LIMITE_HELD_KARP_N:
            respuesta = messagebox.askyesno(
                "Advertencia de Complejidad Asintótica",
                f"Has seleccionado N = {n}.\n"
                f"La complejidad de Held-Karp es O(n² · 2ⁿ).\n"
                f"Para N={n}, se evaluarán ~{n*n*(2**n):,} operaciones.\n"
                f"¿Deseas continuar de todas formas?",
            )
            if not respuesta:
                return

        self.btn_ejecutar_hk.config(state="disabled")
        self.progreso_hk.start(10)
        self.txt_res_hk.delete("1.0", tk.END)
        self.txt_res_hk.insert(tk.END, "Calculando Held-Karp y Greedy en segundo plano...\n")

        hilo = threading.Thread(target=self._hilo_held_karp, args=(n,), daemon=True)
        hilo.start()

    def _hilo_held_karp(self, n: int):
        sub_pedidos = self.pedidos[:n]
        coords = [(p.lat, p.lon) for p in sub_pedidos]

        # 1. Ejecutar Held-Karp
        idx_hk, dist_hk, t_hk = held_karp_tsp(coords, retornar_al_inicio=True)

        # 2. Ejecutar Greedy en los mismos puntos
        # Usamos el nodo del primer pedido como punto de partida
        origen_id = sub_pedidos[0].nodo_id
        ruta_greedy = vecino_mas_cercano(
            nodo_inicio_id=origen_id,
            pedidos=sub_pedidos[1:],
            grafo=self.grafo,
            retornar_al_inicio=True,
        )

        secuencia_nodos_hk = [sub_pedidos[i].nodo_id for i in idx_hk]

        # Actualizar GUI en el hilo principal
        self.after(
            0,
            self._finalizar_held_karp,
            n,
            secuencia_nodos_hk,
            dist_hk,
            t_hk,
            ruta_greedy,
        )

    def _finalizar_held_karp(
        self,
        n: int,
        secuencia_hk: List[str],
        dist_hk: float,
        t_hk: float,
        ruta_greedy,
    ):
        self.progreso_hk.stop()
        self.btn_ejecutar_hk.config(state="normal")

        # Dibujar grafo y ambas rutas en mapa
        self.mapa_hk.dibujar_grafo()

        # Resaltar ruta Greedy en verde tenue
        self.mapa_hk.resaltar_ruta(
            ruta_greedy.secuencia_nodos,
            color="#10b981",
            ancho=3,
            nombre_ruta="Ruta Greedy",
        )

        # Resaltar ruta Held-Karp en púrpura intenso
        self.mapa_hk.resaltar_ruta(
            secuencia_hk,
            color="#7c3aed",
            ancho=5,
            nombre_ruta="Ruta Held-Karp Óptima",
        )

        diff_dist = ruta_greedy.distancia_total_m - dist_hk
        pct_desv = (diff_dist / dist_hk * 100.0) if dist_hk > 0 else 0.0

        self.txt_res_hk.delete("1.0", tk.END)
        self.txt_res_hk.insert(tk.END, "=== COMPARATIVA TSP: HELD-KARP vs GREEDY ===\n\n")
        self.txt_res_hk.insert(tk.END, f"Puntos evaluados: N = {n}\n\n")
        self.txt_res_hk.insert(tk.END, "--- 1. Held-Karp (Óptimo Global) ---\n")
        self.txt_res_hk.insert(tk.END, f"• Distancia: {dist_hk:,.2f} m\n")
        self.txt_res_hk.insert(tk.END, f"• Tiempo de cómputo: {t_hk:.3f} ms\n")
        self.txt_res_hk.insert(tk.END, f"• Complejidad: O(n² 2ⁿ)\n\n")

        self.txt_res_hk.insert(tk.END, "--- 2. Greedy (Heurística Voraz) ---\n")
        self.txt_res_hk.insert(tk.END, f"• Distancia: {ruta_greedy.distancia_total_m:,.2f} m\n")
        self.txt_res_hk.insert(tk.END, f"• Tiempo de cómputo: {ruta_greedy.tiempo_computo_ms:.3f} ms\n")
        self.txt_res_hk.insert(tk.END, f"• Complejidad: O(n²)\n\n")

        self.txt_res_hk.insert(tk.END, "--- 3. Conclusión Comparativa ---\n")
        if diff_dist > 0:
            self.txt_res_hk.insert(
                tk.END,
                f"• Held-Karp ahorra {diff_dist:,.1f} m ({pct_desv:.1f}% más corto que Greedy).\n",
            )
        else:
            self.txt_res_hk.insert(tk.END, "• Greedy logró alcanzar el óptimo en este caso.\n")

        speedup = (t_hk / max(ruta_greedy.tiempo_computo_ms, 0.001))
        self.txt_res_hk.insert(
            tk.END,
            f"• Greedy fue {speedup:.1f}x más rápido, pero Held-Karp garantiza el óptimo matemático.\n",
        )
