"""
Pestaña de Comparación y Benchmarks Algorítmicos.
Incrusta gráficos interactivos de Matplotlib en Tkinter alimentados con datos empíricos reales:
- Tiempo de Ejecución vs N (Escala Logarítmica): Greedy O(n²) vs Held-Karp O(n² 2ⁿ)
- Calidad de Solución: Distancia Greedy vs Distancia Óptima Held-Karp (Gap de optimalidad)
- Métricas empíricas de poda en Backtracking y tabla de análisis asintótico Big-O.
"""

import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from benchmarks.benchmark import ejecutar_todo_y_guardar


class TabComparacion(ttk.Frame):
    """Pestaña para análisis empírico y comparativa Big-O entre paradigmas."""

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.ruta_json = Path(__file__).resolve().parent.parent / "benchmarks" / "resultados_benchmark.json"

        self._crear_interfaz()
        self._cargar_y_dibujar_graficos()

    def _crear_interfaz(self):
        panel_top = ttk.Frame(self, padding=(12, 8))
        panel_top.pack(fill=tk.X)

        ttk.Label(
            panel_top,
            text="Comparación Empírica y Análisis Asintótico (Big-O)",
            font=("Segoe UI", 13, "bold"),
            foreground="#1e3a8a",
        ).pack(side=tk.LEFT)

        self.btn_ejecutar_bench = ttk.Button(
            panel_top,
            text="🔄 Ejecutar Benchmark en Vivo",
            command=self._lanzar_benchmark_hilo,
        )
        self.btn_ejecutar_bench.pack(side=tk.RIGHT, padx=5)

        self.lbl_estado_bench = ttk.Label(
            panel_top,
            text="Datos de benchmark cargados",
            font=("Segoe UI", 9, "italic"),
            foreground="#475569",
        )
        self.lbl_estado_bench.pack(side=tk.RIGHT, padx=10)

        # Contenedor central dividido: izquierda gráficos, derecha tabla resumen
        panel_central = ttk.Frame(self, padding=8)
        panel_central.pack(fill=tk.BOTH, expand=True)

        # Área de gráficos Matplotlib
        self.frame_grafico = ttk.Frame(panel_central)
        self.frame_grafico.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.figura = Figure(figsize=(7.5, 5.0), dpi=100)
        self.canvas_matplot = FigureCanvasTkAgg(self.figura, master=self.frame_grafico)
        self.canvas_matplot.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Panel lateral derecho: Tabla comparativa de complejidades
        panel_der = ttk.LabelFrame(panel_central, text="Resumen Formal de Complejidad", width=360, padding=10)
        panel_der.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        columnas = ("algo", "tiempo", "espacio")
        self.tabla_bigo = ttk.Treeview(panel_der, columns=columnas, show="headings", height=8)
        self.tabla_bigo.heading("algo", text="Algoritmo")
        self.tabla_bigo.heading("tiempo", text="Tiempo (Big-O)")
        self.tabla_bigo.heading("espacio", text="Espacio")

        self.tabla_bigo.column("algo", width=125)
        self.tabla_bigo.column("tiempo", width=120, anchor="center")
        self.tabla_bigo.column("espacio", width=80, anchor="center")
        self.tabla_bigo.pack(fill=tk.X, pady=4)

        datos_bigo = [
            ("Merge Sort", "O(n log n)", "O(n)"),
            ("Quick Sort", "O(n log n) prom", "O(log n)"),
            ("Búsq. Binaria", "O(log n)", "O(1)"),
            ("Greedy (TSP)", "O(n²)", "O(n)"),
            ("Divide & Vence", "O(n log n)", "O(n)"),
            ("Mochila (PD)", "O(N · W)", "O(N · W)"),
            ("Held-Karp (PD)", "O(n² 2ⁿ)", "O(n 2ⁿ)"),
            ("Backtracking", "O(V!) podado", "O(V)"),
        ]
        for row in datos_bigo:
            self.tabla_bigo.insert("", tk.END, values=row)

        # Métricas de Backtracking de la corrida
        self.frame_metricas_bt = ttk.LabelFrame(panel_der, text="Resultados de Backtracking con Poda", padding=8)
        self.frame_metricas_bt.pack(fill=tk.BOTH, expand=True, pady=8)

        self.txt_bt_info = tk.Text(self.frame_metricas_bt, height=7, width=35, font=("Consolas", 8))
        self.txt_bt_info.pack(fill=tk.BOTH, expand=True)

        # Explicación de sustentación
        lbl_info = ttk.Label(
            panel_der,
            text=(
                "Conclusiones para la Defensa:\n"
                "• Greedy: O(n²) escalable, respuesta instantánea, con un gap de ineficiencia de ~10-15%.\n"
                "• Held-Karp: Óptimo estricto, pero su costo exponencial O(n² 2ⁿ) limita N ≤ 12-14.\n"
                "• Backtracking: Garantiza explorar todas las alternativas y evita calles cortadas, con poda drástica."
            ),
            wraplength=330,
            font=("Segoe UI", 8),
            foreground="#1e293b",
        )
        lbl_info.pack(anchor="w", pady=(8, 0))

    def _cargar_y_dibujar_graficos(self):
        if not self.ruta_json.exists():
            return

        with open(self.ruta_json, "r", encoding="utf-8") as f:
            datos = json.load(f)

        tsp = datos.get("tsp_comparativa", {})
        ns = tsp.get("n", [])
        t_greedy = tsp.get("tiempo_greedy_ms", [])
        t_hk = tsp.get("tiempo_held_karp_ms", [])
        d_greedy = tsp.get("distancia_greedy_m", [])
        d_hk = tsp.get("distancia_held_karp_m", [])

        self.figura.clear()

        # Gráfico 1: Tiempo vs N (Escala logarítmica)
        ax1 = self.figura.add_subplot(211)
        ax1.plot(ns, t_greedy, "o-", label="Greedy O(n²)", color="#059669", linewidth=2)
        ax1.plot(ns, t_hk, "s-", label="Held-Karp O(n² 2ⁿ)", color="#7c3aed", linewidth=2)
        ax1.set_title("Tiempo de Cómputo vs Cantidad de Entregas N (Empírico)", fontsize=10, fontweight="bold")
        ax1.set_ylabel("Tiempo (ms)", fontsize=8)
        ax1.set_yscale("log")
        ax1.grid(True, linestyle="--", alpha=0.6)
        ax1.legend(fontsize=8)

        # Anotación en N=12
        if len(ns) >= 5:
            ax1.annotate(
                f"{t_hk[-1]:.1f} ms",
                (ns[-1], t_hk[-1]),
                textcoords="offset points",
                xytext=(-20, 7),
                fontsize=7,
                fontweight="bold",
                color="#7c3aed",
            )

        # Gráfico 2: Calidad de Ruta (Distancia total en metros)
        ax2 = self.figura.add_subplot(212)
        ax2.plot(ns, d_greedy, "o--", label="Distancia Greedy (Heurística)", color="#059669", linewidth=1.8)
        ax2.plot(ns, d_hk, "s-", label="Distancia Held-Karp (Óptima)", color="#e11d48", linewidth=2.0)
        ax2.set_title("Calidad de Solución: Distancia Total de Reparto (m)", fontsize=10, fontweight="bold")
        ax2.set_xlabel("N (Puntos de Entrega)", fontsize=8)
        ax2.set_ylabel("Distancia (m)", fontsize=8)
        ax2.grid(True, linestyle="--", alpha=0.6)
        ax2.legend(fontsize=8)

        self.figura.tight_layout()
        self.canvas_matplot.draw()

        # Actualizar datos de Backtracking
        bt = datos.get("backtracking", {}).get("casos_backtracking", [])
        self.txt_bt_info.delete("1.0", tk.END)
        for c in bt:
            self.txt_bt_info.insert(
                tk.END,
                f"• {c['par']}: {c['rutas_encontradas']} rutas | {c['ramas_podadas']} podas | {c['distancia_optima_m']}m ({c['tiempo_ms']}ms)\n",
            )

    def _lanzar_benchmark_hilo(self):
        self.btn_ejecutar_bench.config(state="disabled")
        self.lbl_estado_bench.config(text="Ejecutando benchmarks reales...")

        def _tarea():
            ejecutar_todo_y_guardar(self.ruta_json)
            self.after(0, self._finalizar_benchmark)

        hilo = threading.Thread(target=_tarea, daemon=True)
        hilo.start()

    def _finalizar_benchmark(self):
        self._cargar_y_dibujar_graficos()
        self.btn_ejecutar_bench.config(state="normal")
        self.lbl_estado_bench.config(text="Benchmarks actualizados con éxito")
        messagebox.showinfo("Éxito", "Benchmarks ejecutados y gráficos actualizados con datos reales.")
