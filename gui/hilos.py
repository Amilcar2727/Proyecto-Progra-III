"""
Ejecución de cálculos largos en segundo plano sin congelar la interfaz.

Tkinter no es seguro entre hilos: un hilo secundario NO debe tocar widgets ni llamar
a widget.after(). Por eso el hilo de trabajo solo deja su resultado en una cola
(queue.Queue, que sí es segura entre hilos) y el hilo principal la revisa cada 50 ms
con after(). Así la ventana sigue respondiendo mientras el algoritmo corre.
"""

import queue
import threading
from typing import Any, Callable, Optional


def ejecutar_en_segundo_plano(
    widget,
    trabajo: Callable[[], Any],
    al_terminar: Callable[[Any], None],
    al_fallar: Optional[Callable[[BaseException], None]] = None,
    intervalo_ms: int = 50,
) -> None:
    """
    Corre `trabajo()` en un hilo daemon y entrega su resultado a `al_terminar`
    en el hilo de Tkinter. Si `trabajo` lanza una excepción, se entrega a `al_fallar`.
    """
    buzon: "queue.Queue[tuple]" = queue.Queue(maxsize=1)

    def _hilo():
        try:
            buzon.put(("ok", trabajo()))
        except BaseException as error:  # se reporta en la GUI, no se pierde en consola
            buzon.put(("error", error))

    def _revisar():
        try:
            estado, valor = buzon.get_nowait()
        except queue.Empty:
            if widget.winfo_exists():
                widget.after(intervalo_ms, _revisar)
            return
        if not widget.winfo_exists():
            return
        if estado == "ok":
            al_terminar(valor)
        elif al_fallar is not None:
            al_fallar(valor)
        else:
            raise valor

    threading.Thread(target=_hilo, daemon=True).start()
    widget.after(intervalo_ms, _revisar)
