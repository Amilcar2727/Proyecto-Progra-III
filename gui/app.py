"""
Ventana Principal de la Aplicación.
Gestiona el ciclo de vida de la GUI, carga de datos y las pestañas del sistema.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import config
from core.gestor_datos import cargar_grafo, cargar_pedidos, cargar_repartidores
from gui.tab_mapa import TabMapa
from gui.tab_pedidos import TabPedidos
from gui.tab_greedy import TabGreedy
from gui.tab_dyv import TabDyV
from gui.tab_pd import TabPD
from gui.tab_backtracking import TabBacktracking
from gui.tab_comparacion import TabComparacion


class AppRutasCusco(tk.Tk):
    """Ventana raíz del Sistema de Gestión de Rutas Óptimas en Cusco."""

    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestión de Rutas Óptimas en Cusco — UNSAAC Progra III")
        self.geometry("1240x760")
        self.minsize(1000, 650)

        # Cargar datos del modelo
        try:
            self.grafo = cargar_grafo()
            self.pedidos = cargar_pedidos()
            self.repartidores = cargar_repartidores()
        except Exception as e:
            messagebox.showerror(
                "Error de Inicialización",
                f"No se pudieron cargar los datos iniciales:\n{e}",
            )
            self.destroy()
            return

        self._configurar_estilos()
        self._construir_interfaz()

    def _configurar_estilos(self):
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        # Configuración de tipografía y colores limpios
        self.style.configure(".", font=("Segoe UI", 9))
        self.style.configure("TNotebook", tabmargins=[4, 4, 4, 0])
        self.style.configure(
            "TNotebook.Tab",
            padding=[12, 6],
            font=("Segoe UI", 9, "bold"),
        )
        self.style.configure("TButton", font=("Segoe UI", 9), padding=4)
        self.style.configure("TLabelframe.Label", font=("Segoe UI", 9, "bold"), foreground="#1e293b")

    def _construir_interfaz(self):
        # Barra superior con título
        frame_header = ttk.Frame(self, padding=(14, 8), style="Header.TFrame")
        frame_header.pack(side=tk.TOP, fill=tk.X)

        lbl_titulo = ttk.Label(
            frame_header,
            text="OptiRutas Cusco",
            font=("Segoe UI", 16, "bold"),
            foreground="#1e3a8a",
        )
        lbl_titulo.pack(side=tk.LEFT)

        lbl_subtitulo = ttk.Label(
            frame_header,
            text="Optimización Multiparadigma: Greedy • Divide & Vence • Prog. Dinámica • Backtracking",
            font=("Segoe UI", 9, "italic"),
            foreground="#475569",
        )
        lbl_subtitulo.pack(side=tk.LEFT, padx=(15, 0), pady=(4, 0))

        # Notebook con pestañas
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 4))

        # 1. Pestaña Red Vial
        self.tab_mapa = TabMapa(
            self.notebook,
            grafo=self.grafo,
            al_hacer_clic_mapa=self._al_hacer_clic_mapa,
        )
        self.notebook.add(self.tab_mapa, text="  🗺️ Red Vial Cusco  ")

        # 2. Pestaña Pedidos
        self.tab_pedidos = TabPedidos(
            self.notebook, pedidos=self.pedidos, grafo=self.grafo
        )
        self.notebook.add(self.tab_pedidos, text="  📦 Pedidos  ")

        # 3. Pestaña Greedy
        self.tab_greedy = TabGreedy(
            self.notebook,
            grafo=self.grafo,
            pedidos=self.pedidos,
            repartidores=self.repartidores,
        )
        self.notebook.add(self.tab_greedy, text="  ⚡ Greedy  ")

        # 4. Pestaña Divide y Vencerás
        self.tab_dyv = TabDyV(
            self.notebook, grafo=self.grafo, pedidos=self.pedidos
        )
        self.notebook.add(self.tab_dyv, text="  ➗ Divide & Vence  ")

        # 5. Pestaña Programación Dinámica
        self.tab_pd = TabPD(
            self.notebook, grafo=self.grafo, pedidos=self.pedidos
        )
        self.notebook.add(self.tab_pd, text="  🧠 Prog. Dinámica  ")

        # 6. Pestaña Backtracking
        self.tab_backtracking = TabBacktracking(
            self.notebook, grafo=self.grafo
        )
        self.notebook.add(self.tab_backtracking, text="  🔍 Backtracking  ")

        # 7. Pestaña Comparación & Benchmarks
        self.tab_comparacion = TabComparacion(self.notebook)
        self.notebook.add(self.tab_comparacion, text="  📊 Comparación Big-O  ")

        # Barra de estado inferior
        frame_status = ttk.Frame(self, relief=tk.SUNKEN, padding=(10, 4))
        frame_status.pack(side=tk.BOTTOM, fill=tk.X)

        self.lbl_status = ttk.Label(
            frame_status,
            text=f"Sistema Listo | {len(self.grafo.nodos)} Nodos cargados | {len(self.pedidos)} Pedidos | {len(self.repartidores)} Repartidores activos",
            font=("Segoe UI", 8),
            foreground="#334155",
        )
        self.lbl_status.pack(side=tk.LEFT)

        lbl_unsaac = ttk.Label(
            frame_status,
            text="UNSAAC • Ingeniería Informática y de Sistemas",
            font=("Segoe UI", 8, "italic"),
            foreground="#64748b",
        )
        lbl_unsaac.pack(side=tk.RIGHT)

    def _al_hacer_clic_mapa(self, coordenadas):
        """Abre un alta de pedido precargada con las coordenadas seleccionadas."""
        self.tab_pedidos.abrir_formulario_alta(coordenadas)
