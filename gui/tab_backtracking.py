"""
Pestaña de Backtracking (Búsqueda Exhaustiva) con Poda opcional.
Encuentra las rutas simples entre origen y destino evitando calles cerradas,
permite activar/desactivar la poda Branch & Bound y cerrar/reabrir calles,
e inspeccionar cada ruta en el mapa.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional, Tuple
import config
from core.modelos import Grafo
from core.backtracking import buscar_rutas_backtracking, ResultadoBacktracking
from gui.componente_mapa import ComponenteMapa
from gui.panel_desplazable import crear_panel_lateral
from gui.hilos import ejecutar_en_segundo_plano


class TabBacktracking(ttk.Frame):
    """Pestaña para cálculo exhaustivo de rutas con manejo de calles bloqueadas."""

    def __init__(self, master, grafo: Grafo, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.grafo = grafo
        self.rutas_actuales: List[Tuple[List[str], float]] = []
        self.ocupado = False

        self._crear_interfaz()

    # ------------------------------------------------------------------ interfaz
    def _crear_interfaz(self):
        panel_izq = crear_panel_lateral(self, ancho=350, padding=10)

        ttk.Label(
            panel_izq,
            text="Backtracking (Búsqueda Exhaustiva)",
            font=("Segoe UI", 13, "bold"),
            foreground="#b45309",
        ).pack(anchor="w", pady=(0, 4))

        ttk.Label(
            panel_izq,
            text=(
                "Recorre en profundidad todos los caminos simples: avanza a un vecino no "
                "visitado por una calle abierta y, al agotar sus opciones, retrocede."
            ),
            wraplength=320,
            font=("Segoe UI", 8),
            foreground="#475569",
        ).pack(anchor="w", pady=(0, 6))

        nodos_lista = [f"{n.id}: {n.nombre}" for n in self.grafo.nodos.values()]

        # --- Origen / destino
        frame_sel = ttk.LabelFrame(panel_izq, text="1. Origen y destino", padding=8)
        frame_sel.pack(fill=tk.X, pady=3)

        self.cb_origen = ttk.Combobox(frame_sel, values=nodos_lista, state="readonly")
        self.cb_destino = ttk.Combobox(frame_sel, values=nodos_lista, state="readonly")
        ttk.Label(frame_sel, text="Origen:").grid(row=0, column=0, sticky="w")
        self.cb_origen.grid(row=0, column=1, sticky="ew", pady=1)
        ttk.Label(frame_sel, text="Destino:").grid(row=1, column=0, sticky="w")
        self.cb_destino.grid(row=1, column=1, sticky="ew", pady=1)
        frame_sel.columnconfigure(1, weight=1)
        self._fijar_escenario_enunciado()

        ttk.Button(
            frame_sel,
            text="Caso del enunciado: San Blas → Wanchaq",
            command=self._fijar_escenario_enunciado,
        ).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        # --- Calles cerradas
        frame_calle = ttk.LabelFrame(panel_izq, text="2. Calles cerradas por mantenimiento", padding=8)
        frame_calle.pack(fill=tk.X, pady=3)

        ttk.Label(
            frame_calle,
            text="Elige dos lugares conectados o haz clic sobre una calle en el mapa.",
            wraplength=310,
            font=("Segoe UI", 8, "italic"),
        ).grid(row=0, column=0, columnspan=2, sticky="w")
        self.cb_calle_a = ttk.Combobox(frame_calle, values=nodos_lista, state="readonly", width=16)
        self.cb_calle_b = ttk.Combobox(frame_calle, values=nodos_lista, state="readonly", width=16)
        self.cb_calle_a.grid(row=1, column=0, sticky="ew", padx=(0, 2), pady=2)
        self.cb_calle_b.grid(row=1, column=1, sticky="ew", pady=2)
        self.cb_calle_a.bind("<<ComboboxSelected>>", self._actualizar_vecinos_combo)
        frame_calle.columnconfigure(0, weight=1)
        frame_calle.columnconfigure(1, weight=1)

        self.btn_alternar = ttk.Button(
            frame_calle, text="Cerrar / reabrir", command=self._alternar_desde_combos
        )
        self.btn_alternar.grid(row=2, column=0, sticky="ew", padx=(0, 2))
        self.btn_cerrar_optima = ttk.Button(
            frame_calle,
            text="Cerrar tramo de la óptima",
            command=self._cerrar_calle_de_optima,
        )
        self.btn_cerrar_optima.grid(row=2, column=1, sticky="ew")
        self.btn_reabrir = ttk.Button(
            frame_calle, text="Reabrir todas las calles", command=self._reabrir_todas
        )
        self.btn_reabrir.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(3, 0))
        self.lbl_cerradas = ttk.Label(
            frame_calle, text="Cerradas: ninguna", wraplength=310, foreground="#b91c1c",
            font=("Segoe UI", 8),
        )
        self.lbl_cerradas.grid(row=4, column=0, columnspan=2, sticky="w", pady=(3, 0))

        # --- Ejecución
        frame_run = ttk.LabelFrame(panel_izq, text="3. Ejecutar", padding=8)
        frame_run.pack(fill=tk.X, pady=3)

        self.var_poda = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame_run,
            text="Usar poda por cota (Branch & Bound)",
            variable=self.var_poda,
        ).pack(anchor="w")
        ttk.Label(
            frame_run,
            text=(
                "Sin poda se listan TODAS las rutas. Con poda se descartan ramas cuyo costo "
                "parcial ya iguala o supera la mejor ruta: misma óptima, menos estados."
            ),
            wraplength=310,
            font=("Segoe UI", 7),
            foreground="#64748b",
        ).pack(anchor="w")

        self.btn_buscar_rutas = ttk.Button(
            frame_run, text="Buscar rutas", command=self._lanzar_backtracking
        )
        self.btn_buscar_rutas.pack(fill=tk.X, pady=(6, 2))
        self.progreso_bt = ttk.Progressbar(frame_run, mode="indeterminate")
        self.progreso_bt.pack(fill=tk.X)

        # --- Métricas
        self.frame_metricas = ttk.LabelFrame(panel_izq, text="Métricas del árbol de estados", padding=6)
        self.frame_metricas.pack(fill=tk.X, pady=3)
        self.lbl_metricas = ttk.Label(
            self.frame_metricas, text="Aún no se ejecutó la búsqueda.", font=("Consolas", 8),
            justify=tk.LEFT,
        )
        self.lbl_metricas.pack(anchor="w")

        # --- Lista de rutas
        frame_lista = ttk.LabelFrame(panel_izq, text="Rutas encontradas (clic para ver en el mapa)", padding=6)
        frame_lista.pack(fill=tk.BOTH, expand=True, pady=3)
        self.lista_rutas = tk.Listbox(frame_lista, font=("Consolas", 8), height=6)
        scroll = ttk.Scrollbar(frame_lista, orient=tk.VERTICAL, command=self.lista_rutas.yview)
        self.lista_rutas.configure(yscrollcommand=scroll.set)
        self.lista_rutas.bind("<<ListboxSelect>>", self._al_seleccionar_ruta_lista)
        self.lista_rutas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Mapa
        self.componente_mapa = ComponenteMapa(
            self,
            grafo=self.grafo,
            al_hacer_clic_arista=self._al_hacer_clic_calle,
        )
        self.componente_mapa.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.componente_mapa.dibujar_grafo()
        self._actualizar_lbl_cerradas()

    # ------------------------------------------------------------------ utilidades
    @staticmethod
    def _id_de(seleccion: str) -> str:
        return seleccion.split(":")[0].strip()

    def _fijar_escenario_enunciado(self):
        valores = list(self.cb_origen["values"])
        for combo, nodo_id in ((self.cb_origen, "N02"), (self.cb_destino, "N11")):
            for i, v in enumerate(valores):
                if v.startswith(nodo_id + ":"):
                    combo.current(i)

    def _actualizar_vecinos_combo(self, _evento=None):
        """Al elegir el lugar A, el combo B ofrece solo los lugares conectados a A."""
        a = self._id_de(self.cb_calle_a.get())
        vecinos = sorted(set(self.grafo.adyacencia.get(a, {})) | {
            u for u, vs in self.grafo.adyacencia.items() if a in vs
        })
        self.cb_calle_b["values"] = [f"{v}: {self.grafo.nodos[v].nombre}" for v in vecinos]
        if vecinos:
            self.cb_calle_b.current(0)

    def _actualizar_lbl_cerradas(self):
        cerradas = self.grafo.calles_cerradas()
        texto = ", ".join(f"{u}–{v}" for u, v in cerradas) if cerradas else "ninguna"
        self.lbl_cerradas.config(text=f"Cerradas: {texto}")

    def _alternar_calle(self, u: str, v: str):
        if self.ocupado:
            return
        cerrada = self.grafo.esta_bloqueada(u, v) or self.grafo.esta_bloqueada(v, u)
        if not self.grafo.cambiar_estado_calle(u, v, activa=cerrada):
            messagebox.showinfo("Aviso", f"No existe una conexión directa entre {u} y {v}.")
            return
        self._actualizar_lbl_cerradas()
        if self.rutas_actuales:
            self._lanzar_backtracking()  # recalcular con la nueva restricción
        else:
            self.componente_mapa.dibujar_grafo()

    def _alternar_desde_combos(self):
        a, b = self.cb_calle_a.get(), self.cb_calle_b.get()
        if not a or not b:
            messagebox.showwarning("Atención", "Elige los dos extremos de la calle.")
            return
        self._alternar_calle(self._id_de(a), self._id_de(b))

    def _cerrar_calle_de_optima(self):
        """Demostración rápida: cierra el primer tramo de la ruta óptima y recalcula."""
        if not self.rutas_actuales:
            messagebox.showinfo("Atención", "Primero busca las rutas.")
            return
        camino = self.rutas_actuales[0][0]
        self._alternar_calle(camino[0], camino[1])

    def _reabrir_todas(self):
        if self.ocupado:
            return
        for u, v in self.grafo.calles_cerradas():
            self.grafo.cambiar_estado_calle(u, v, activa=True)
        self._actualizar_lbl_cerradas()
        self.componente_mapa.dibujar_grafo()

    def _al_hacer_clic_calle(self, u_id: str, v_id: str):
        self._alternar_calle(u_id, v_id)

    def refrescar(self):
        """Llamado al entrar a la pestaña: refleja calles cerradas desde otras pestañas."""
        self._actualizar_lbl_cerradas()
        if self.componente_mapa.esta_desactualizado():
            self.componente_mapa.dibujar_grafo()
            self.rutas_actuales = []
            self.lista_rutas.delete(0, tk.END)

    # ------------------------------------------------------------------ ejecución
    def _lanzar_backtracking(self):
        if self.ocupado:
            return
        sel_orig, sel_dest = self.cb_origen.get(), self.cb_destino.get()
        if not sel_orig or not sel_dest:
            messagebox.showwarning("Atención", "Elige origen y destino.")
            return
        u, v = self._id_de(sel_orig), self._id_de(sel_dest)
        if u == v:
            messagebox.showwarning("Atención", "El origen y destino deben ser nodos distintos.")
            return

        usar_poda = self.var_poda.get()
        self._fijar_ocupado(True)
        ejecutar_en_segundo_plano(
            self,
            lambda: buscar_rutas_backtracking(
                grafo=self.grafo,
                origen_id=u,
                destino_id=v,
                max_rutas=config.LIMITE_BACKTRACKING_RUTAS,
                timeout_seg=config.TIMEOUT_BACKTRACKING_SEG,
                usar_poda=usar_poda,
            ),
            lambda res: self._finalizar_backtracking(res, usar_poda),
            self._fallo_backtracking,
        )

    def _fijar_ocupado(self, ocupado: bool):
        self.ocupado = ocupado
        estado = "disabled" if ocupado else "normal"
        for boton in (self.btn_buscar_rutas, self.btn_alternar, self.btn_cerrar_optima, self.btn_reabrir):
            boton.config(state=estado)
        if ocupado:
            self.progreso_bt.start(10)
        else:
            self.progreso_bt.stop()

    def _fallo_backtracking(self, error: BaseException):
        self._fijar_ocupado(False)
        messagebox.showerror("Backtracking", f"No se pudo completar la búsqueda:\n{error}")

    def _finalizar_backtracking(self, resultado: ResultadoBacktracking, usar_poda: bool):
        self._fijar_ocupado(False)
        self.rutas_actuales = resultado.rutas_encontradas

        modo = "con poda" if usar_poda else "sin poda (exhaustiva)"
        lineas = [
            f"Modo: {modo}",
            f"Rutas {'mejorantes' if usar_poda else 'simples'} encontradas: {len(self.rutas_actuales)}",
            f"Estados visitados: {resultado.total_estados_visitados}",
            f"Ramas podadas por cota: {resultado.total_ramas_podadas}",
            f"Tiempo de cómputo: {resultado.tiempo_computo_ms:.3f} ms",
        ]
        if resultado.ruta_optima:
            lineas.append(f"Ruta más corta: {resultado.ruta_optima[1]:,.1f} m")
        if resultado.limite_alcanzado:
            lineas.append(
                f"⚠ Se alcanzó el límite ({config.LIMITE_BACKTRACKING_RUTAS} rutas o "
                f"{config.TIMEOUT_BACKTRACKING_SEG:.0f} s): la lista está incompleta."
            )
        self.lbl_metricas.config(text="\n".join(lineas))

        self.lista_rutas.delete(0, tk.END)
        for idx, (camino, dist) in enumerate(self.rutas_actuales):
            prefijo = "★ " if idx == 0 else f"{idx + 1:>2}. "
            self.lista_rutas.insert(tk.END, f"{prefijo}{dist:>8,.1f} m  {' → '.join(camino)}")

        self.componente_mapa.dibujar_grafo()
        if resultado.ruta_optima:
            self.componente_mapa.resaltar_camino_aristas(
                resultado.ruta_optima[0],
                color=config.COLOR_RUTA_OPTIMA,
                ancho=5,
                nombre_ruta="Ruta más corta",
            )
            self.lista_rutas.select_set(0)
        else:
            messagebox.showinfo(
                "Sin conexión",
                "No existe ninguna ruta con las calles actualmente abiertas.",
            )

    def _al_seleccionar_ruta_lista(self, _evento):
        sel = self.lista_rutas.curselection()
        if not sel or sel[0] >= len(self.rutas_actuales):
            return
        idx = sel[0]
        camino, _ = self.rutas_actuales[idx]
        self.componente_mapa.dibujar_grafo()
        color = config.COLOR_RUTA_OPTIMA if idx == 0 else config.COLOR_RUTA_BACKTRACKING
        self.componente_mapa.resaltar_camino_aristas(camino, color=color, ancho=5, nombre_ruta=f"Ruta #{idx + 1}")
