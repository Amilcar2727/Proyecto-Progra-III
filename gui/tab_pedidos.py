"""
Pestaña de Gestión y Consulta de Pedidos.
Integra algoritmos manuales de ordenación (Merge Sort, Quick Sort),
búsqueda O(1) por ID, búsqueda binaria O(log n) e índice invertido por sector.
Permite dar de alta nuevos pedidos mediante formulario.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Tuple
from core.modelos import Grafo, Pedido
from core.estructuras import (
    merge_sort,
    quick_sort,
    busqueda_binaria,
    construir_indice_id,
    construir_indice_invertido_sector,
)
from core.geo import nodo_mas_cercano_haversine
from core.grafo import obtener_matriz_distancias


class TabPedidos(ttk.Frame):
    """Pestaña que visualiza y administra los pedidos de reparto."""

    def __init__(self, master, pedidos: List[Pedido], grafo: Grafo, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.pedidos = pedidos
        self.grafo = grafo
        self.pedidos_actuales = list(pedidos)

        # Construcción de índices para búsquedas eficientes
        self._actualizar_indices()
        self._crear_interfaz()
        self.refrescar_tabla(self.pedidos_actuales)

    def _actualizar_indices(self):
        self.indice_id = construir_indice_id(self.pedidos)
        self.indice_sector = construir_indice_invertido_sector(self.pedidos)

    def _crear_interfaz(self):
        # Panel superior: Acciones y filtros
        panel_top = ttk.Frame(self, padding=(10, 8))
        panel_top.pack(fill=tk.X)

        ttk.Label(
            panel_top,
            text="Gestión y Análisis de Pedidos",
            font=("Segoe UI", 13, "bold"),
            foreground="#1e3a8a",
        ).pack(side=tk.LEFT)

        btn_nuevo = ttk.Button(
            panel_top,
            text="➕ Nuevo Pedido",
            command=self.abrir_formulario_alta,
        )
        btn_nuevo.pack(side=tk.RIGHT, padx=5)

        self.lbl_total = ttk.Label(
            panel_top,
            text=f"Total: {len(self.pedidos)} pedidos",
            font=("Segoe UI", 10, "italic"),
        )
        self.lbl_total.pack(side=tk.RIGHT, padx=10)

        # Panel de Ordenación y Búsqueda
        self.frame_algos = ttk.LabelFrame(self, text="Operaciones de Ordenación y Búsqueda (Algoritmos Manuales)", padding=10)
        self.frame_algos.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(self.frame_algos, text="Algoritmo:").grid(row=0, column=0, sticky="w", padx=4)
        self.combo_sort = ttk.Combobox(
            self.frame_algos,
            values=["Merge Sort (O(n log n))", "Quick Sort (O(n log n))"],
            state="readonly",
            width=23,
        )
        self.combo_sort.current(0)
        self.combo_sort.grid(row=0, column=1, padx=4)

        ttk.Label(self.frame_algos, text="Criterio:").grid(row=0, column=2, sticky="w", padx=4)
        self.combo_criterio = ttk.Combobox(
            self.frame_algos,
            values=[
                "Prioridad (1: Alta a 3: Baja)",
                "Valor (Soles desc)",
                "Peso (Kg asc)",
                "Distancia al Centro (m asc)",
            ],
            state="readonly",
            width=25,
        )
        self.combo_criterio.current(0)
        self.combo_criterio.grid(row=0, column=3, padx=4)

        self.btn_ordenar = ttk.Button(self.frame_algos, text="Ordenar Lista", command=self._al_ordenar)
        self.btn_ordenar.grid(row=0, column=4, padx=6)

        # Fila 2: Búsquedas
        ttk.Label(self.frame_algos, text="Buscar:").grid(row=1, column=0, sticky="w", padx=4, pady=(8, 0))
        self.entry_busqueda = ttk.Entry(self.frame_algos, width=25)
        self.entry_busqueda.grid(row=1, column=1, padx=4, pady=(8, 0))

        self.combo_tipo_busq = ttk.Combobox(
            self.frame_algos,
            values=[
                "Por ID (O(1) Hash Dict)",
                "Búsqueda Binaria por ID O(log n)",
                "Por Sector (Índice Invertido)",
            ],
            state="readonly",
            width=28,
        )
        self.combo_tipo_busq.current(0)
        self.combo_tipo_busq.grid(row=1, column=2, columnspan=2, sticky="w", padx=4, pady=(8, 0))

        self.btn_buscar = ttk.Button(self.frame_algos, text="Buscar", command=self._al_buscar)
        self.btn_buscar.grid(row=1, column=4, padx=6, pady=(8, 0))

        self.btn_restablecer = ttk.Button(self.frame_algos, text="Ver Todos", command=self._restablecer_lista)
        self.btn_restablecer.grid(row=1, column=5, padx=4, pady=(8, 0))

        # Tabla de pedidos
        frame_tabla = ttk.Frame(self, padding=10)
        frame_tabla.pack(fill=tk.BOTH, expand=True)

        columnas = ("id", "cliente", "nodo", "sector", "prioridad", "peso", "volumen", "valor", "dist_centro")
        self.tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=15)

        self.tabla.heading("id", text="ID Pedido")
        self.tabla.heading("cliente", text="Cliente / Destino")
        self.tabla.heading("nodo", text="Nodo Ref.")
        self.tabla.heading("sector", text="Sector")
        self.tabla.heading("prioridad", text="Prioridad")
        self.tabla.heading("peso", text="Peso (kg)")
        self.tabla.heading("volumen", text="Vol. (L)")
        self.tabla.heading("valor", text="Valor (S/.)")
        self.tabla.heading("dist_centro", text="Dist. Plaza por calles (m)")

        self.tabla.column("id", width=85, anchor="center")
        self.tabla.column("cliente", width=200)
        self.tabla.column("nodo", width=85, anchor="center")
        self.tabla.column("sector", width=125)
        self.tabla.column("prioridad", width=85, anchor="center")
        self.tabla.column("peso", width=80, anchor="e")
        self.tabla.column("volumen", width=80, anchor="e")
        self.tabla.column("valor", width=95, anchor="e")
        self.tabla.column("dist_centro", width=105, anchor="e")

        scroll_y = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL, command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        self.tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

    def refrescar_tabla(self, lista_pedidos: List[Pedido]):
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        prioridades_texto = {1: "1 - Urgente", 2: "2 - Media", 3: "3 - Baja"}
        matriz = obtener_matriz_distancias(self.grafo)
        for p in lista_pedidos:
            d_centro = matriz["N01"][p.nodo_id]
            self.tabla.insert(
                "",
                tk.END,
                values=(
                    p.id,
                    p.cliente,
                    p.nodo_id,
                    p.sector,
                    prioridades_texto.get(p.prioridad, str(p.prioridad)),
                    f"{p.peso_kg:.1f}",
                    f"{p.volumen_l:.1f}",
                    f"S/. {p.valor_soles:.2f}",
                    f"{d_centro:,.1f}" if d_centro != float("inf") else "Inalcanzable",
                ),
            )
        self.lbl_total.config(text=f"Mostrando: {len(lista_pedidos)} pedidos")

    def _al_ordenar(self):
        algo_seleccionado = self.combo_sort.get()
        criterio = self.combo_criterio.get()

        # Determinar clave y dirección según criterio
        if "Prioridad" in criterio:
            key_func = lambda p: p.prioridad
            reverse = False
        elif "Valor" in criterio:
            key_func = lambda p: p.valor_soles
            reverse = True
        elif "Peso" in criterio:
            key_func = lambda p: p.peso_kg
            reverse = False
        else:  # Distancia al Centro
            matriz = obtener_matriz_distancias(self.grafo)
            key_func = lambda p: matriz["N01"][p.nodo_id]
            reverse = False

        if "Merge Sort" in algo_seleccionado:
            ordenados = merge_sort(self.pedidos_actuales, key=key_func, reverse=reverse)
            nombre_algo = "Merge Sort O(n log n)"
        else:
            ordenados = quick_sort(self.pedidos_actuales, key=key_func, reverse=reverse)
            nombre_algo = "Quick Sort O(n log n)"

        self.pedidos_actuales = ordenados
        self.refrescar_tabla(self.pedidos_actuales)
        messagebox.showinfo(
            "Ordenación Completa",
            f"Se ordenaron {len(ordenados)} pedidos usando {nombre_algo} a mano con criterio '{criterio}'.",
        )

    def _al_buscar(self):
        termino = self.entry_busqueda.get().strip()
        if not termino:
            messagebox.showwarning("Atención", "Ingresa un término de búsqueda.")
            return

        tipo = self.combo_tipo_busq.get()

        if "Por ID (O(1)" in tipo:
            pedido = self.indice_id.get(termino.upper())
            if pedido:
                self.refrescar_tabla([pedido])
                messagebox.showinfo("Búsqueda O(1) Hash", f"Pedido {pedido.id} encontrado: {pedido.cliente}")
            else:
                messagebox.showinfo("Búsqueda O(1) Hash", f"No se encontró el pedido con ID '{termino}'.")

        elif "Búsqueda Binaria" in tipo:
            # Requisito de búsqueda binaria: arreglo ordenado por clave
            pedidos_por_id = quick_sort(self.pedidos, key=lambda p: p.id)
            idx = busqueda_binaria(pedidos_por_id, termino.upper(), key=lambda p: p.id)
            if idx != -1:
                pedido = pedidos_por_id[idx]
                self.refrescar_tabla([pedido])
                messagebox.showinfo(
                    "Búsqueda Binaria O(log n)",
                    f"Pedido {pedido.id} encontrado en índice ordenado {idx} en O(log n) comparaciones.",
                )
            else:
                messagebox.showinfo("Búsqueda Binaria O(log n)", f"ID '{termino}' no hallado en la lista.")

        elif "Por Sector" in tipo:
            resultados = []
            for sector_nombre, lista in self.indice_sector.items():
                if termino.lower() in sector_nombre.lower():
                    resultados.extend(lista)

            if resultados:
                self.refrescar_tabla(resultados)
                messagebox.showinfo(
                    "Índice Invertido O(1)",
                    f"Se encontraron {len(resultados)} pedidos para el sector '{termino}'.",
                )
            else:
                messagebox.showinfo("Índice Invertido", f"No hay pedidos en sectores que coincidan con '{termino}'.")

    def _restablecer_lista(self):
        self.pedidos_actuales = list(self.pedidos)
        self.refrescar_tabla(self.pedidos_actuales)

    def abrir_formulario_alta(
        self, coordenadas: Optional[Tuple[float, float]] = None
    ):
        """Ventana modal para registrar un nuevo pedido."""
        ventana = tk.Toplevel(self)
        ventana.title("Registrar Nuevo Pedido")
        ventana.geometry("400x520")
        ventana.transient(self)
        ventana.grab_set()

        frame = ttk.Frame(ventana, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Alta de Pedido de Reparto", font=("Segoe UI", 12, "bold")).pack(pady=(0, 10))

        nuevo_id = f"PED-{len(self.pedidos) + 1:03d}"

        ttk.Label(frame, text=f"ID Asignado: {nuevo_id}", font=("Segoe UI", 9, "italic")).pack(anchor="w")

        ttk.Label(frame, text="Nombre del Cliente:").pack(anchor="w", pady=(8, 0))
        entry_cliente = ttk.Entry(frame, width=35)
        entry_cliente.insert(0, "Cliente Ejemplo")
        entry_cliente.pack(fill=tk.X, pady=2)

        latitud_inicial, longitud_inicial = coordenadas or (-13.5167, -71.9788)
        ttk.Label(frame, text="Latitud del pedido:").pack(anchor="w", pady=(8, 0))
        entry_lat = ttk.Entry(frame, width=18)
        entry_lat.insert(0, str(latitud_inicial))
        entry_lat.pack(anchor="w", pady=2)

        ttk.Label(frame, text="Longitud del pedido:").pack(anchor="w", pady=(6, 0))
        entry_lon = ttk.Entry(frame, width=18)
        entry_lon.insert(0, str(longitud_inicial))
        entry_lon.pack(anchor="w", pady=2)
        lbl_asignacion = ttk.Label(
            frame,
            text="El nodo de interés más cercano se asignará al guardar.",
            wraplength=360,
            foreground="#475569",
        )
        lbl_asignacion.pack(anchor="w", pady=(2, 0))

        ttk.Label(frame, text="Prioridad (1: Urgente, 2: Media, 3: Baja):").pack(anchor="w", pady=(8, 0))
        spin_prio = ttk.Spinbox(frame, from_=1, to=3, width=5)
        spin_prio.set("2")
        spin_prio.pack(anchor="w", pady=2)

        ttk.Label(frame, text="Peso (kg):").pack(anchor="w", pady=(8, 0))
        entry_peso = ttk.Entry(frame, width=10)
        entry_peso.insert(0, "3.5")
        entry_peso.pack(anchor="w", pady=2)

        ttk.Label(frame, text="Volumen (Litros):").pack(anchor="w", pady=(8, 0))
        entry_vol = ttk.Entry(frame, width=10)
        entry_vol.insert(0, "5.0")
        entry_vol.pack(anchor="w", pady=2)

        ttk.Label(frame, text="Valor Comercial (S/.):").pack(anchor="w", pady=(8, 0))
        entry_valor = ttk.Entry(frame, width=10)
        entry_valor.insert(0, "85.0")
        entry_valor.pack(anchor="w", pady=2)

        def _guardar():
            cliente = entry_cliente.get().strip()
            if not cliente:
                messagebox.showerror("Error", "El cliente es obligatorio.")
                return
            try:
                prio = int(spin_prio.get())
                peso = float(entry_peso.get())
                vol = float(entry_vol.get())
                val = float(entry_valor.get())
                lat = float(entry_lat.get())
                lon = float(entry_lon.get())
            except ValueError:
                messagebox.showerror("Error", "Valores numéricos inválidos.")
                return
            if not -90 <= lat <= 90 or not -180 <= lon <= 180:
                messagebox.showerror("Error", "Latitud o longitud fuera de rango.")
                return

            nid, distancia_asignacion = nodo_mas_cercano_haversine(
                lat, lon, self.grafo.nodos.values()
            )
            nodo_obj = self.grafo.nodos[nid]

            p = Pedido(
                id=nuevo_id,
                cliente=cliente,
                nodo_id=nid,
                lat=lat,
                lon=lon,
                sector=nodo_obj.sector,
                prioridad=prio,
                peso_kg=peso,
                volumen_l=vol,
                valor_soles=val,
            )
            self.pedidos.append(p)
            self._actualizar_indices()
            self._restablecer_lista()
            messagebox.showinfo(
                "Éxito",
                f"Pedido {nuevo_id} registrado y asignado a {nodo_obj.id}: "
                f"{nodo_obj.nombre} ({distancia_asignacion:.1f} m en línea recta).",
            )
            ventana.destroy()

        btn_guardar = ttk.Button(frame, text="Guardar Pedido", command=_guardar)
        btn_guardar.pack(fill=tk.X, pady=(15, 0))
