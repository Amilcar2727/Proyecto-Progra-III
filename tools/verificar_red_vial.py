"""Imprime métricas de desvío y dibuja el cache vial para inspección visual."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from core.geo import distancia_haversine  # noqa: E402


OUTPUT_PNG = ROOT / "data" / "red_vial_verificacion.png"


def verificar() -> None:
    ruta_cache = config.RED_VIAL_CACHE_FILE
    if not ruta_cache.exists():
        raise FileNotFoundError(
            f"No existe {ruta_cache}. Ejecute primero "
            "`python tools/construir_red_vial.py` con acceso a Overpass."
        )
    with ruta_cache.open(encoding="utf-8") as archivo:
        cache = json.load(archivo)

    nodos = {nodo["id"]: nodo for nodo in cache["nodos"]}
    print(f"{'Arista':<14} {'Haversine (m)':>16} {'Red (m)':>14} {'Factor':>10}")
    print("-" * 58)
    for arista in cache["aristas"]:
        origen = nodos[arista["origen"]]
        destino = nodos[arista["destino"]]
        directa = distancia_haversine(
            origen["lat_original"],
            origen["lon_original"],
            destino["lat_original"],
            destino["lon_original"],
        )
        red = float(arista["longitud_m"])
        factor = red / directa if directa else float("inf")
        print(
            f"{arista['origen']}->{arista['destino']:<9} "
            f"{directa:16.2f} {red:14.2f} {factor:10.3f}"
        )

    fig, ax = plt.subplots(figsize=(11, 9))
    for arista in cache["aristas"]:
        puntos = arista["geometria"]
        if len(puntos) >= 2:
            ax.plot(
                [p[1] for p in puntos],
                [p[0] for p in puntos],
                color="#667085",
                linewidth=0.8,
                alpha=0.55,
                zorder=1,
            )
    for nodo in cache["nodos"]:
        ax.scatter(nodo["lon_ajustado"], nodo["lat_ajustado"], s=18, color="#dc2626", zorder=3)
        ax.annotate(
            nodo["id"],
            (nodo["lon_ajustado"], nodo["lat_ajustado"]),
            xytext=(3, 3),
            textcoords="offset points",
            fontsize=7,
        )
    ax.set_title("Grafo de interés y geometrías de rutas por calles")
    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    OUTPUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PNG, dpi=180)
    plt.close(fig)
    print(f"\nPNG de inspección: {OUTPUT_PNG}")
    print(f"Atribución: {cache.get('metadatos', {}).get('atribucion', '© OpenStreetMap contributors')}")


if __name__ == "__main__":
    verificar()
