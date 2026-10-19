"""
Punto de Entrada Principal del Sistema de Gestión de Rutas Óptimas en Cusco.
Proyecto de Algoritmos Avanzados - Programación III (UNSAAC Cusco).
"""

import sys
from gui.app import AppRutasCusco


def main():
    """Inicializa el ciclo principal de la aplicación."""
    try:
        app = AppRutasCusco()
        app.mainloop()
    except KeyboardInterrupt:
        print("\nAplicación finalizada por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[Error Crítico]: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
