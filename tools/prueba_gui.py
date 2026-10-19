"""
Prueba de humo de la interfaz: abre la aplicación, pulsa cada funcionalidad de cada
pestaña y comprueba que nada lance errores ni deje la ventana bloqueada.

Uso:
    python tools/prueba_gui.py                 # solo verifica
    python tools/prueba_gui.py --capturas DIR  # además guarda capturas PNG de cada pestaña

Las ventanas emergentes (messagebox) se reemplazan por registros en consola para que la
prueba no se detenga esperando un clic.
"""

import argparse
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tkinter as tk  # noqa: E402
from tkinter import messagebox  # noqa: E402

MENSAJES = []


def _registrar(tipo):
    def _f(titulo="", mensaje="", **_kw):
        MENSAJES.append((tipo, titulo, mensaje))
        print(f"  [{tipo}] {titulo}: {str(mensaje)[:90]}")
        return True
    return _f


for _nombre in ("showinfo", "showwarning", "showerror", "askyesno"):
    setattr(messagebox, _nombre, _registrar(_nombre))

from gui.app import AppRutasCusco  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capturas", type=Path, default=None)
    args = parser.parse_args()
    if args.capturas:
        args.capturas.mkdir(parents=True, exist_ok=True)

    app = AppRutasCusco()
    app.geometry("1366x800+0+0")
    errores = []
    original = app.report_callback_exception

    def _capturar_error(tipo, valor, tb):
        errores.append(f"{tipo.__name__}: {valor}")
        traceback.print_exception(tipo, valor, tb)

    app.report_callback_exception = _capturar_error

    def esperar(segundos=0.6, hasta=None, limite=30.0):
        """Procesa eventos (incluidos los resultados de hilos) sin bloquear."""
        inicio = time.time()
        while True:
            app.update()
            transcurrido = time.time() - inicio
            if hasta is None and transcurrido >= segundos:
                return
            if hasta is not None and hasta():
                app.update()
                return
            if transcurrido > limite:
                raise TimeoutError("La operación no terminó a tiempo (¿GUI colgada?)")
            time.sleep(0.02)

    def ir_a(pestana):
        app.notebook.select(pestana)
        esperar(0.4)

    def capturar(nombre):
        if not args.capturas:
            return
        from PIL import ImageGrab
        esperar(0.5)
        x, y = app.winfo_rootx(), app.winfo_rooty()
        w, h = app.winfo_width(), app.winfo_height()
        ImageGrab.grab(bbox=(x, y, x + w, y + h), xdisplay=None).save(args.capturas / f"{nombre}.png")
        print(f"  captura -> {nombre}.png")

    pasos = []

    def paso(nombre):
        def deco(f):
            pasos.append((nombre, f))
            return f
        return deco

    @paso("Mapa: cerrar y reabrir una calle con los combos")
    def _():
        t = app.tab_mapa
        ir_a(t)
        capturar("captura_01_mapa_inicial")
        a = next(iter(app.grafo.adyacencia))
        b = next(iter(app.grafo.adyacencia[a]))
        for combo, nid in ((t.cb_nodo_a, a), (t.cb_nodo_b, b)):
            combo.set(f"{nid}: {app.grafo.nodos[nid].nombre}")
        t._alternar_calle_desde_combos()
        assert app.grafo.esta_bloqueada(a, b)
        t._alternar_calle_desde_combos()
        assert not app.grafo.esta_bloqueada(a, b)

    @paso("Pedidos: ordenar con Merge y Quick Sort por cada criterio")
    def _():
        t = app.tab_pedidos
        ir_a(t)
        for algo in range(2):
            for criterio in range(4):
                t.combo_sort.current(algo)
                t.combo_criterio.current(criterio)
                t._al_ordenar()
        t.combo_sort.current(0)
        t.combo_criterio.current(0)
        t._al_ordenar()
        prioridades = [p.prioridad for p in t.pedidos_actuales]
        assert prioridades == sorted(prioridades)
        capturar("captura_02_tabla_pedidos")

    @paso("Pedidos: búsqueda hash, binaria y por sector")
    def _():
        t = app.tab_pedidos
        for tipo, termino, esperado in ((0, "PED-005", 1), (1, "ped-010", 1), (2, "Wanchaq", None), (0, "XX-999", 0)):
            t.combo_tipo_busq.current(tipo)
            t.entry_busqueda.delete(0, tk.END)
            t.entry_busqueda.insert(0, termino)
            t._al_buscar()
            filas = len(t.tabla.get_children())
            if esperado is not None:
                assert filas == esperado, (termino, filas)
            else:
                assert filas > 0
        t._restablecer_lista()

    @paso("Pedidos: alta de un pedido nuevo (y validación de datos inválidos)")
    def _():
        t = app.tab_pedidos
        antes = len(app.pedidos)
        t.abrir_formulario_alta((-13.5205, -71.9672))
        esperar(0.3)
        ventana = [w for w in t.winfo_children() if isinstance(w, tk.Toplevel)][-1]
        entradas = [w for w in ventana.winfo_children()[0].winfo_children() if w.winfo_class() in ("TEntry", "TSpinbox")]
        peso = entradas[4]
        peso.delete(0, tk.END)
        peso.insert(0, "-2")
        boton = [w for w in ventana.winfo_children()[0].winfo_children() if w.winfo_class() == "TButton"][-1]
        boton.invoke()
        assert len(app.pedidos) == antes, "aceptó un peso negativo"
        peso.delete(0, tk.END)
        peso.insert(0, "3.5")
        boton.invoke()
        esperar(0.3)
        assert len(app.pedidos) == antes + 1
        assert len({p.id for p in app.pedidos}) == len(app.pedidos), "IDs repetidos"

    @paso("Greedy: vecino más cercano y despacho de emergencia")
    def _():
        t = app.tab_greedy
        ir_a(t)
        t.spin_n.set("31")
        t._ejecutar_vecino_cercano()
        assert "RESULTADOS GREEDY" in t.txt_resultados.get("1.0", tk.END)
        t.spin_n.set("8")
        t._ejecutar_vecino_cercano()
        capturar("captura_03_ruta_greedy")
        t._ejecutar_asignacion_emergencia()
        assert "Repartidor Asignado" in t.txt_resultados.get("1.0", tk.END)

    @paso("Divide y Vencerás: una zona por repartidor y zonas de K")
    def _():
        t = app.tab_dyv
        ir_a(t)
        t.var_modo.set("k")
        t._al_cambiar_modo()
        t._ejecutar_dyv()
        assert "ZONAS DE K" in t.txt_zonas.get("1.0", tk.END)
        t.var_modo.set("repartidores")
        t._al_cambiar_modo()
        t._ejecutar_dyv()
        assert "UNA ZONA POR REPARTIDOR" in t.txt_zonas.get("1.0", tk.END)
        capturar("captura_04_dyv_repartidores")

    @paso("Programación Dinámica: mochila por repartidor y Held-Karp")
    def _():
        t = app.tab_pd
        ir_a(t)
        t.cb_repartidor.current(0)
        t._al_elegir_repartidor()
        t.spin_n_mochila.set("15")
        t._ejecutar_mochila()
        texto = t.txt_res_mochila.get("1.0", tk.END)
        assert "Valor máximo" in texto
        cap = float(t.spin_peso_max.get())
        filas = t.tabla_dp.get_children()
        assert len(filas) == 16
        t.spin_peso_max.set("12.5")
        t._ejecutar_mochila()
        t.spin_peso_max.set(str(cap))
        t._ejecutar_mochila()
        t.tab_mochila.master.select(t.tab_mochila)
        capturar("captura_07_knapsack_seleccion")
        t.tab_held_karp.master.select(t.tab_held_karp)
        t.spin_n_hk.set("8")
        t._lanzar_hilo_held_karp()
        esperar(hasta=lambda: str(t.btn_ejecutar_hk["state"]) == "normal")
        assert "HELD-KARP" in t.txt_res_hk.get("1.0", tk.END)
        capturar("captura_05_ruta_held_karp")
        t.tab_mochila.master.select(t.tab_mochila)

    @paso("Backtracking: San Blas -> Wanchaq sin poda, con poda y con calle cerrada")
    def _():
        t = app.tab_backtracking
        ir_a(t)
        t._fijar_escenario_enunciado()
        t.var_poda.set(False)
        t._lanzar_backtracking()
        esperar(hasta=lambda: not t.ocupado)
        sin_poda = len(t.rutas_actuales)
        assert sin_poda == 27, sin_poda
        optima = t.rutas_actuales[0]
        t.var_poda.set(True)
        t._lanzar_backtracking()
        esperar(hasta=lambda: not t.ocupado)
        assert t.rutas_actuales[0] == optima
        t.var_poda.set(False)
        t._lanzar_backtracking()
        esperar(hasta=lambda: not t.ocupado)
        t._cerrar_calle_de_optima()
        esperar(hasta=lambda: not t.ocupado)
        assert app.grafo.calles_cerradas()
        assert t.rutas_actuales and t.rutas_actuales[0][1] >= optima[1]
        cerrada = app.grafo.calles_cerradas()[0]
        for camino, _ in t.rutas_actuales:
            pares = set(zip(camino, camino[1:]))
            assert cerrada not in pares and cerrada[::-1] not in pares
        capturar("captura_06_backtracking_bloqueo")

    @paso("Otras pestañas ven la calle cerrada; reabrir todo")
    def _():
        ir_a(app.tab_greedy)
        assert not app.tab_greedy.componente_mapa.esta_desactualizado()
        ir_a(app.tab_mapa)
        assert "1" in app.tab_mapa.lbl_bloqueadas.cget("text") or app.grafo.calles_cerradas()
        ir_a(app.tab_backtracking)
        app.tab_backtracking._reabrir_todas()
        assert not app.grafo.calles_cerradas()

    @paso("Comparación: gráficos y benchmark en vivo")
    def _():
        t = app.tab_comparacion
        ir_a(t)
        t._lanzar_benchmark()
        esperar(hasta=lambda: str(t.btn_ejecutar_bench["state"]) == "normal", limite=120)
        assert "Greedy vs Held-Karp" in t.txt_conclusiones.get("1.0", tk.END)
        capturar("captura_08_comparacion")

    fallidos = 0
    for nombre, funcion in pasos:
        print(f"- {nombre}")
        try:
            funcion()
            esperar(0.2)
            print("  OK")
        except Exception:
            fallidos += 1
            traceback.print_exc()
            print("  FALLÓ")

    app.report_callback_exception = original
    print(f"\nMapa en modo sin conexión (Canvas): {app.tab_mapa.componente_mapa.modo_fallback}")
    print(f"Pasos fallidos: {fallidos} | Errores en callbacks: {len(errores)}")
    errores_msg = [m for m in MENSAJES if m[0] == "showerror"]
    print(f"Ventanas de error mostradas: {len(errores_msg)}")
    app.destroy()
    return 1 if (fallidos or errores) else 0


if __name__ == "__main__":
    sys.exit(main())
