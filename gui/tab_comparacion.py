"""
Pestaña de Comparación y Benchmarks Algorítmicos.
Incrusta gráficos de Matplotlib en Tkinter alimentados con mediciones reales
(benchmarks/resultados_benchmark.json):
- TSP: tiempo y calidad de Greedy O(n²) frente a Held-Karp O(n² 2ⁿ).
- Backtracking: estados visitados con y sin poda.
- Mochila: valor de la PD exacta frente a la heurística voraz.
Además muestra la tabla Big-O y conclusiones calculadas a partir de los datos.
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from benchmarks.benchmark import ejecutar_todo_y_guardar
from gui.hilos import ejecutar_en_segundo_plano

DATOS_BIGO = [
    ("Merge Sort", "O(n log n)", "O(n)"),
    ("Quick Sort", "O(n log n) prom.", "O(log n)"),
    ("Búsq. binaria", "O(log n)", "O(1)"),
    ("Búsq. hash por ID", "O(1) prom.", "O(n)"),
    ("Dijkstra (V veces)", "O(V(V+E) log V)", "O(V²)"),
    ("Greedy vecino cercano", "O(n²)", "O(n)"),
    ("Greedy emergencia", "O(R)", "O(1)"),
    ("D&C partición K", "Θ(n log² n)", "O(n)"),
    ("D&C ruta zonas K", "O(n²/K)", "O(n)"),
    ("D&C R zonas", "Θ(n log n log R)", "O(n)"),
    ("Mochila 0/1 (PD)", "O(N·W)", "O(N·W)"),
    ("Held-Karp (PD)", "O(n² 2ⁿ)", "O(n 2ⁿ)"),
    ("Backtracking", "O(b^d)", "O(V)"),
]


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
            text="Comparación empírica y análisis asintótico (Big-O)",
            font=("Segoe UI", 13, "bold"),
            foreground="#1e3a8a",
        ).pack(side=tk.LEFT)

        self.btn_ejecutar_bench = ttk.Button(
            panel_top,
            text="🔄 Ejecutar benchmark en vivo",
            command=self._lanzar_benchmark,
        )
        self.btn_ejecutar_bench.pack(side=tk.RIGHT, padx=5)

        self.progreso = ttk.Progressbar(panel_top, mode="indeterminate", length=120)
        self.progreso.pack(side=tk.RIGHT, padx=5)

        self.lbl_estado_bench = ttk.Label(
            panel_top,
            text="",
            font=("Segoe UI", 9, "italic"),
            foreground="#475569",
        )
        self.lbl_estado_bench.pack(side=tk.RIGHT, padx=10)

        panel_central = ttk.Frame(self, padding=8)
        panel_central.pack(fill=tk.BOTH, expand=True)

        self.frame_grafico = ttk.Frame(panel_central)
        self.frame_grafico.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.figura = Figure(figsize=(8.0, 5.4), dpi=100)
        self.canvas_matplot = FigureCanvasTkAgg(self.figura, master=self.frame_grafico)
        self.canvas_matplot.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        panel_der = ttk.LabelFrame(panel_central, text="Resumen de complejidad", width=380, padding=8)
        panel_der.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        columnas = ("algo", "tiempo", "espacio")
        self.tabla_bigo = ttk.Treeview(panel_der, columns=columnas, show="headings", height=len(DATOS_BIGO))
        self.tabla_bigo.heading("algo", text="Algoritmo")
        self.tabla_bigo.heading("tiempo", text="Tiempo")
        self.tabla_bigo.heading("espacio", text="Espacio")
        self.tabla_bigo.column("algo", width=128)
        self.tabla_bigo.column("tiempo", width=118, anchor="center")
        self.tabla_bigo.column("espacio", width=66, anchor="center")
        self.tabla_bigo.pack(fill=tk.X, pady=4)
        for fila in DATOS_BIGO:
            self.tabla_bigo.insert("", tk.END, values=fila)

        ttk.Label(
            panel_der,
            text="n: pedidos · V, E: lugares y calles · W: capacidad en 0.1 kg · "
                 "R: repartidores · b, d: ramificación y largo del camino (peor caso del backtracking: O(V·V!))",
            wraplength=350,
            font=("Segoe UI", 7),
            foreground="#64748b",
        ).pack(anchor="w")

        frame_concl = ttk.LabelFrame(panel_der, text="¿Cuándo usar cada enfoque? (según los datos)", padding=6)
        frame_concl.pack(fill=tk.BOTH, expand=True, pady=6)
        self.txt_conclusiones = tk.Text(frame_concl, height=12, width=46, font=("Segoe UI", 8), wrap=tk.WORD)
        self.txt_conclusiones.pack(fill=tk.BOTH, expand=True)

    def _cargar_y_dibujar_graficos(self):
        if not self.ruta_json.exists():
            self.lbl_estado_bench.config(text="Sin datos: ejecuta el benchmark")
            return
        with open(self.ruta_json, "r", encoding="utf-8") as f:
            datos = json.load(f)
        self.lbl_estado_bench.config(text=f"Datos del {datos.get('timestamp', '?')}")

        tsp = datos.get("tsp_comparativa", {})
        ns = tsp.get("n", [])
        bt = datos.get("backtracking", {}).get("casos_backtracking", [])
        mochila = datos.get("mochila", {})

        self.figura.clear()
        ax1 = self.figura.add_subplot(221)
        ax2 = self.figura.add_subplot(222)
        ax3 = self.figura.add_subplot(223)
        ax4 = self.figura.add_subplot(224)

        # 1. Tiempo TSP (log)
        ax1.plot(ns, tsp.get("tiempo_greedy_ms", []), "o-", label="Greedy O(n²)", color="#059669")
        ax1.plot(ns, tsp.get("tiempo_held_karp_ms", []), "s-", label="Held-Karp O(n²2ⁿ)", color="#7c3aed")
        ax1.set_yscale("log")
        ax1.set_title("Tiempo TSP vs N", fontsize=9, fontweight="bold")
        ax1.set_xlabel("N puntos", fontsize=7)
        ax1.set_ylabel("ms (escala log)", fontsize=7)
        ax1.legend(fontsize=7)

        # 2. Calidad TSP
        ax2.plot(ns, tsp.get("distancia_greedy_m", []), "o--", label="Greedy", color="#059669")
        ax2.plot(ns, tsp.get("distancia_held_karp_m", []), "s-", label="Held-Karp (óptimo)", color="#e11d48")
        ax2.set_title("Distancia del recorrido TSP", fontsize=9, fontweight="bold")
        ax2.set_xlabel("N puntos", fontsize=7)
        ax2.set_ylabel("metros", fontsize=7)
        ax2.legend(fontsize=7)

        # 3. Backtracking con y sin poda
        if bt:
            etiquetas = [c["par"].replace(" -> ", "→") for c in bt]
            x = list(range(len(bt)))
            sin = [c.get("estados_visitados_sin_poda", 0) for c in bt]
            con = [c.get("estados_visitados", 0) for c in bt]
            ax3.bar([i - 0.2 for i in x], sin, width=0.4, label="Sin poda", color="#f59e0b")
            ax3.bar([i + 0.2 for i in x], con, width=0.4, label="Con poda", color="#b45309")
            ax3.set_xticks(x)
            ax3.set_xticklabels(etiquetas, fontsize=6)
            ax3.legend(fontsize=7)
        ax3.set_title("Backtracking: estados visitados", fontsize=9, fontweight="bold")

        # 4. Mochila PD vs voraz
        if mochila:
            ax4.plot(mochila["n"], mochila["valor_pd"], "s-", label="PD (óptimo)", color="#6b21a8")
            ax4.plot(mochila["n"], mochila["valor_voraz"], "o--", label="Greedy valor/kg", color="#059669")
            ax4.legend(fontsize=7)
            ax4.set_xlabel("N pedidos", fontsize=7)
            ax4.set_ylabel("S/.", fontsize=7)
        ax4.set_title(f"Mochila {mochila.get('capacidad_kg', '')} kg: valor cargado", fontsize=9, fontweight="bold")

        for ax in (ax1, ax2, ax3, ax4):
            ax.grid(True, linestyle="--", alpha=0.5)
            ax.tick_params(labelsize=7)
        self.figura.tight_layout()
        self.canvas_matplot.draw()

        self._escribir_conclusiones(datos)

    def _escribir_conclusiones(self, datos: dict):
        tsp = datos.get("tsp_comparativa", {})
        bt = datos.get("backtracking", {}).get("casos_backtracking", [])
        mochila = datos.get("mochila", {})
        zonas = datos.get("zonas_repartidores", {})
        t = self.txt_conclusiones
        t.delete("1.0", tk.END)

        if tsp.get("n"):
            gaps = tsp.get("gap_porcentaje", [])
            t.insert(
                tk.END,
                f"• Greedy vs Held-Karp: Greedy es instantáneo pero su ruta fue hasta "
                f"{max(gaps):.1f}% más larga que la óptima. Held-Karp tardó "
                f"{tsp['tiempo_held_karp_ms'][-1]:.1f} ms con N = {tsp['n'][-1]}; entre N = {tsp['n'][1]} y "
                f"N = {tsp['n'][-1]} su tiempo se multiplicó por "
                f"{tsp['tiempo_held_karp_ms'][-1] / max(tsp['tiempo_held_karp_ms'][1], 1e-9):.0f}. "
                "Usar PD hasta N ≈ 12-14; Greedy por encima o en emergencias.\n\n",
            )
        if mochila.get("n"):
            dif = [pd - vz for pd, vz in zip(mochila["valor_pd"], mochila["valor_voraz"])]
            t.insert(
                tk.END,
                f"• Mochila: la PD nunca cargó menos valor que el voraz; la diferencia máxima fue "
                f"S/. {max(dif):.2f}. Con capacidad de {mochila['capacidad_kg']} kg la tabla tiene "
                f"hasta {max(mochila['celdas_tabla']):,} celdas y tarda ~1 ms: aquí siempre conviene la PD.\n\n",
            )
        if bt:
            ahorro = [
                1 - c["estados_visitados"] / c["estados_visitados_sin_poda"]
                for c in bt if c.get("estados_visitados_sin_poda")
            ]
            t.insert(
                tk.END,
                f"• Backtracking: es el único que lista TODAS las rutas alternativas y respeta "
                f"cualquier restricción. La poda redujo los estados visitados hasta en "
                f"{max(ahorro) * 100:.0f}% sin perder la óptima, pero el peor caso sigue siendo "
                "exponencial: útil en grafos pequeños o con restricciones duras.\n\n",
            )
        if zonas:
            t.insert(
                tk.END,
                f"• Divide y Vencerás: con una zona por repartidor el equipo recorre "
                f"{zonas['distancia_total_equipo_m'] / 1000:.1f} km en total (la ruta más larga, "
                f"{zonas['ruta_mas_larga_m'] / 1000:.1f} km) frente a "
                f"{zonas['un_repartidor_greedy_m'] / 1000:.1f} km de un solo repartidor voraz.\n",
            )

    def _lanzar_benchmark(self):
        self.btn_ejecutar_bench.config(state="disabled")
        self.progreso.start(10)
        self.lbl_estado_bench.config(text="Ejecutando benchmarks reales...")
        ejecutar_en_segundo_plano(
            self,
            lambda: ejecutar_todo_y_guardar(self.ruta_json),
            lambda _datos: self._finalizar_benchmark(),
            self._fallo_benchmark,
        )

    def _fallo_benchmark(self, error: BaseException):
        self.progreso.stop()
        self.btn_ejecutar_bench.config(state="normal")
        self.lbl_estado_bench.config(text="El benchmark falló")
        messagebox.showerror("Benchmark", f"No se pudo ejecutar el benchmark:\n{error}")

    def _finalizar_benchmark(self):
        self.progreso.stop()
        self.btn_ejecutar_bench.config(state="normal")
        self._cargar_y_dibujar_graficos()
