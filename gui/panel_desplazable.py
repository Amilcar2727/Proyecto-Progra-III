"""
Panel lateral con barra de desplazamiento vertical.

En pantallas de laptop (1366x768) los controles de algunas pestañas no entran en
altura; este panel permite desplazarlos con la barra o con la rueda del mouse.
"""

import tkinter as tk
from tkinter import ttk


def crear_panel_lateral(master, ancho: int = 340, padding: int = 10) -> ttk.Frame:
    """
    Empaqueta a la izquierda de `master` un panel desplazable y devuelve el Frame
    interior, donde se colocan los controles igual que en un Frame normal.
    """
    contenedor = ttk.Frame(master)
    contenedor.pack(side=tk.LEFT, fill=tk.Y)

    lienzo = tk.Canvas(contenedor, width=ancho, highlightthickness=0, borderwidth=0)
    barra = ttk.Scrollbar(contenedor, orient=tk.VERTICAL, command=lienzo.yview)
    lienzo.configure(yscrollcommand=barra.set)
    lienzo.pack(side=tk.LEFT, fill=tk.Y)

    interior = ttk.Frame(lienzo, padding=padding)
    ventana = lienzo.create_window((0, 0), window=interior, anchor="nw")

    # Igualar el fondo del lienzo al del tema ttk
    try:
        fondo = ttk.Style(master).lookup("TFrame", "background")
        if fondo:
            lienzo.configure(background=fondo)
    except tk.TclError:
        pass

    def _ajustar(_evento=None):
        lienzo.configure(scrollregion=lienzo.bbox("all"))
        requerido = interior.winfo_reqheight()
        visible = lienzo.winfo_height()
        # La barra solo aparece cuando realmente hace falta
        if requerido > visible > 1:
            if not barra.winfo_ismapped():
                barra.pack(side=tk.RIGHT, fill=tk.Y)
        elif barra.winfo_ismapped():
            barra.pack_forget()
            lienzo.yview_moveto(0)

    def _ancho(evento):
        lienzo.itemconfigure(ventana, width=evento.width)

    interior.bind("<Configure>", _ajustar)
    lienzo.bind("<Configure>", lambda e: (_ancho(e), _ajustar()))

    def _rueda(evento):
        if not barra.winfo_ismapped():
            return
        if getattr(evento, "num", None) == 4:
            paso = -1
        elif getattr(evento, "num", None) == 5:
            paso = 1
        else:
            paso = -1 if evento.delta > 0 else 1
        lienzo.yview_scroll(paso * 3, "units")

    def _activar_rueda(_e):
        lienzo.bind_all("<MouseWheel>", _rueda)
        lienzo.bind_all("<Button-4>", _rueda)
        lienzo.bind_all("<Button-5>", _rueda)

    def _desactivar_rueda(_e):
        lienzo.unbind_all("<MouseWheel>")
        lienzo.unbind_all("<Button-4>")
        lienzo.unbind_all("<Button-5>")

    contenedor.bind("<Enter>", _activar_rueda)
    contenedor.bind("<Leave>", _desactivar_rueda)
    return interior
