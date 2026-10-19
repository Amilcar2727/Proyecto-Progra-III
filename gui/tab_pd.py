"""
Pestaña de Programación Dinámica (PD).
Implementa Mochila 0/1 (Knapsack) con visualización de la matriz DP y reconstrucción,
y Held-Karp (TSP Óptimo con Bitmask y Memoización) comparado contra Greedy
ejecutado en un hilo de fondo (threading) para no congelar la GUI.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
import config
from core.modelos import Grafo, Pedido, Repartidor
from core.prog_dinamica import resolver_mochila_01, held_karp_tsp
from core.greedy import vecino_mas_cercano, mochila_voraz_por_densidad
from core.grafo import matriz_para_nodos
from gui.componente_mapa import ComponenteMapa
from gui.panel_desplazable import crear_panel_lateral
from gui.hilos import ejecutar_en_segundo_plano

ESCALA_MOCHILA = 10  # 10 unidades por kg -> precisión de 0.1 kg


class TabPD(ttk.Frame):
    """Pestaña que contiene Mochila 0/1 y Held-Karp."""

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
        nb_pd = ttk.Notebook(self)
        nb_pd.pack(fill=tk.BOTH, expand=True)

        self.tab_mochila = ttk.Frame(nb_pd, padding=8)
        self.tab_held_karp = ttk.Frame(nb_pd, padding=8)

        nb_pd.add(self.tab_mochila, text="  1. Mochila 0/1 (Carga Óptima)  ")
        nb_pd.add(self.tab_held_karp, text="  2. Held-Karp (TSP Exacto O(n² 2ⁿ))  ")

        self._configurar_subtab_mochila()
        self._configurar_subtab_held_karp()

    def _configurar_subtab_mochila(self):
        panel_izq = crear_panel_lateral(self.tab_mochila, ancho=340, padding=10)

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

        ttk.Label(frame_cap, text="Vehículo (fija la capacidad):").pack(anchor="w")
        self.cb_repartidor = ttk.Combobox(
            frame_cap,
            values=[f"{r.id}: {r.nombre} ({r.cap_peso_kg:g} kg)" for r in self.repartidores]
            + ["Capacidad personalizada"],
            state="readonly",
        )
        self.cb_repartidor.current(len(self.repartidores))
        self.cb_repartidor.bind("<<ComboboxSelected>>", self._al_elegir_repartidor)
        self.cb_repartidor.pack(fill=tk.X, pady=3)

        ttk.Label(frame_cap, text="Capacidad de Carga Máxima (kg, admite 0.1):").pack(anchor="w")
        self.spin_peso_max = ttk.Spinbox(frame_cap, from_=1, to=120, increment=0.5, width=10)
        self.spin_peso_max.set("25")
        self.spin_peso_max.pack(anchor="w", pady=3)

        ttk.Label(frame_cap, text="Pedidos a evaluar (los N primeros):").pack(anchor="w", pady=(4, 0))
        self.spin_n_mochila = ttk.Spinbox(frame_cap, from_=1, to=len(self.pedidos), width=10)
        self.spin_n_mochila.set(str(min(15, len(self.pedidos))))
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
            text=(
                "Filas: pedidos considerados (i) | Columnas: capacidad parcial w. "
                f"La tabla se calcula cada 0.1 kg; aquí se muestra una columna por kg."
            ),
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
        panel_izq = crear_panel_lateral(self.tab_held_karp, ancho=340, padding=10)

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
        self.spin_n_hk = ttk.Spinbox(frame_hk, from_=3, to=min(14, len(self.pedidos)), width=10)
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

    def refrescar(self):
        """Actualiza los límites si se registraron pedidos nuevos."""
        self.spin_n_mochila.config(to=len(self.pedidos))
        self.spin_n_hk.config(to=min(14, len(self.pedidos)))
        if self.mapa_hk.esta_desactualizado():
            self.mapa_hk.dibujar_grafo()

    def _repartidor_elegido(self) -> Optional[Repartidor]:
        idx = self.cb_repartidor.current()
        return self.repartidores[idx] if 0 <= idx < len(self.repartidores) else None

    def _al_elegir_repartidor(self, _evento=None):
        rep = self._repartidor_elegido()
        if rep is not None:
            self.spin_peso_max.set(f"{rep.cap_peso_kg:g}")

    def _ejecutar_mochila(self):
        try:
            w_max = float(self.spin_peso_max.get().replace(",", "."))
            n_items = int(self.spin_n_mochila.get())
        except ValueError:
            messagebox.showerror("Error", "La capacidad y N deben ser números.")
            return
        if w_max <= 0 or n_items <= 0:
            messagebox.showerror("Error", "La capacidad y N deben ser mayores que cero.")
            return

        candidatos = self.pedidos[:n_items]
        valor_opt, seleccionados, dp = resolver_mochila_01(candidatos, w_max, escala=ESCALA_MOCHILA)
        valor_voraz, elegidos_voraz = mochila_voraz_por_densidad(candidatos, w_max)

        peso_total = sum(p.peso_kg for p in seleccionados)
        vol_total = sum(p.volumen_l for p in seleccionados)
        rep = self._repartidor_elegido()

        t = self.txt_res_mochila
        t.delete("1.0", tk.END)
        t.insert(tk.END, "=== MOCHILA 0/1 (PD) ===\n")
        t.insert(tk.END, f"Valor máximo: S/. {valor_opt:,.2f}\n")
        t.insert(tk.END, f"Peso cargado: {peso_total:.1f} / {w_max:g} kg\n")
        t.insert(tk.END, f"Volumen: {vol_total:.1f} L")
        if rep is not None:
            estado = "OK" if vol_total <= rep.cap_vol_l else "EXCEDE"
            t.insert(tk.END, f" / {rep.cap_vol_l:g} L ({estado})")
        t.insert(tk.END, "\n")
        t.insert(tk.END, f"Pedidos elegidos: {len(seleccionados)}/{len(candidatos)}\n")
        t.insert(tk.END, f"Tabla: {len(dp)} x {len(dp[0])} celdas  O(N·W)\n\n")
        for p in seleccionados:
            t.insert(tk.END, f"• {p.id}: {p.peso_kg:.1f} kg -> S/. {p.valor_soles:.1f}\n")

        t.insert(tk.END, "\n--- Comparación con Greedy (valor/kg) ---\n")
        t.insert(tk.END, f"Valor voraz: S/. {valor_voraz:,.2f} ({len(elegidos_voraz)} pedidos)\n")
        diferencia = valor_opt - valor_voraz
        if diferencia > 1e-9:
            t.insert(tk.END, f"La PD obtiene S/. {diferencia:,.2f} más que el voraz.\n")
        else:
            t.insert(tk.END, "En este caso el voraz también llegó al óptimo.\n")
        if rep is not None and vol_total > rep.cap_vol_l:
            t.insert(tk.END, "\nNota: la PD optimiza solo el peso; el volumen se verifica aparte.\n")

        # Matriz DP: una columna por kg (cada ESCALA_MOCHILA columnas reales)
        for item in self.tabla_dp.get_children():
            self.tabla_dp.delete(item)
        indices = list(range(0, len(dp[0]), ESCALA_MOCHILA))
        if indices[-1] != len(dp[0]) - 1:
            indices.append(len(dp[0]) - 1)
        cols = ["Item / w"] + [f"{c / ESCALA_MOCHILA:g}kg" for c in indices]
        self.tabla_dp["columns"] = cols
        for c in cols:
            self.tabla_dp.heading(c, text=c)
            self.tabla_dp.column(c, width=58 if c != "Item / w" else 165, anchor="center", stretch=False)

        elegidos_ids = {p.id for p in seleccionados}
        self.tabla_dp.tag_configure("elegido", background="#ede9fe")
        self.tabla_dp.insert("", tk.END, values=["i=0 (base)"] + [f"{dp[0][c]:.0f}" for c in indices])
        for i in range(1, len(dp)):
            p = candidatos[i - 1]
            marca = " ✓" if p.id in elegidos_ids else ""
            etiqueta = f"i={i} {p.id} ({p.peso_kg:g}kg){marca}"
            self.tabla_dp.insert(
                "", tk.END,
                values=[etiqueta] + [f"{dp[i][c]:.0f}" for c in indices],
                tags=("elegido",) if marca else (),
            )

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

        ejecutar_en_segundo_plano(
            self,
            lambda: self._calcular_held_karp(n),
            lambda datos: self._finalizar_held_karp(*datos),
            lambda error: self._finalizar_held_karp_error(str(error)),
        )

    def _calcular_held_karp(self, n: int):
        """Se ejecuta en el hilo de trabajo: no toca ningún widget."""
        sub_pedidos = self.pedidos[:n]
        matriz = matriz_para_nodos(self.grafo, [p.nodo_id for p in sub_pedidos])

        # 1. Held-Karp (óptimo exacto)
        idx_hk, dist_hk, t_hk = held_karp_tsp(matriz, retornar_al_inicio=True)

        # 2. Greedy sobre los mismos puntos y desde el mismo inicio
        origen_id = sub_pedidos[0].nodo_id
        ruta_greedy = vecino_mas_cercano(
            nodo_inicio_id=origen_id,
            pedidos=sub_pedidos[1:],
            grafo=self.grafo,
            retornar_al_inicio=True,
        )
        secuencia_nodos_hk = [sub_pedidos[i].nodo_id for i in idx_hk]
        return n, secuencia_nodos_hk, dist_hk, t_hk, ruta_greedy

    def _finalizar_held_karp_error(self, mensaje: str):
        self.progreso_hk.stop()
        self.btn_ejecutar_hk.config(state="normal")
        self.txt_res_hk.delete("1.0", tk.END)
        messagebox.showerror("Recorrido no disponible", mensaje)

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
        self.txt_res_hk.insert(tk.END, f"• Distancia por calles: {dist_hk:,.2f} m\n")
        self.txt_res_hk.insert(tk.END, f"• Tiempo de cómputo: {t_hk:.3f} ms\n")
        self.txt_res_hk.insert(tk.END, f"• Complejidad: O(n² 2ⁿ)\n\n")

        self.txt_res_hk.insert(tk.END, "--- 2. Greedy (Heurística Voraz) ---\n")
        self.txt_res_hk.insert(tk.END, f"• Distancia por calles: {ruta_greedy.distancia_total_m:,.2f} m\n")
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
