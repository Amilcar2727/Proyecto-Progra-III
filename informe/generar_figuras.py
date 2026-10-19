"""
Generador de Figuras para el Informe Técnico.
Usa los datos reales de benchmarks/resultados_benchmark.json para producir
3 PNGs de alta resolución en informe/figuras/.

Figuras generadas:
  fig1_tiempo_vs_n.png   — Tiempo de ejecución (ms) vs n en escala log
  fig2_calidad_ruta.png  — Distancia Greedy vs Held-Karp + Gap %
  fig3_backtracking.png  — Rutas encontradas, ramas podadas y estados visitados
"""

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")          # Backend sin GUI, necesario para scripts headless
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# ─── Rutas ────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent.parent
DATA_FILE   = BASE_DIR / "benchmarks" / "resultados_benchmark.json"
FIGURAS_DIR = Path(__file__).resolve().parent / "figuras"
FIGURAS_DIR.mkdir(exist_ok=True)

with open(DATA_FILE, encoding="utf-8") as f:
    data = json.load(f)

# ─── Paleta de colores coherente ──────────────────────────────────────────────
C_GREEDY   = "#2196F3"   # Azul material
C_HK       = "#E91E63"   # Rosa material
C_MERGE    = "#4CAF50"   # Verde
C_BT_RUTAS = "#FF9800"   # Naranja
C_BT_RAMAS = "#9C27B0"   # Violeta
C_BT_EST   = "#607D8B"   # Gris azulado
GRID_ALPHA  = 0.25

plt.rcParams.update({
    "font.family":      "DejaVu Sans",
    "font.size":        11,
    "axes.titlesize":   13,
    "axes.titleweight": "bold",
    "axes.labelsize":   11,
    "xtick.labelsize":  10,
    "ytick.labelsize":  10,
    "legend.fontsize":  10,
    "figure.dpi":       150,
})

# ══════════════════════════════════════════════════════════════════════════════
# FIGURA 1 — Tiempo de ejecución vs n (escala logarítmica)
# ══════════════════════════════════════════════════════════════════════════════
tsp = data["tsp_comparativa"]
n_tsp   = tsp["n"]
t_gr    = tsp["tiempo_greedy_ms"]
t_hk    = tsp["tiempo_held_karp_ms"]

# Líneas teóricas de referencia escaladas
n_ref = np.linspace(min(n_tsp), max(n_tsp), 300)
# Escalar Greedy teórico: O(n²) — ajuste al primer punto real
k_gr  = t_gr[0] / (n_tsp[0] ** 2)
ref_gr = k_gr * n_ref ** 2
# Escalar Held-Karp teórico: O(2^n * n^2) — ajuste al primer punto real
k_hk  = t_hk[0] / ((2 ** n_tsp[0]) * (n_tsp[0] ** 2))
ref_hk = k_hk * (2 ** n_ref) * (n_ref ** 2)

fig1, ax1 = plt.subplots(figsize=(8, 5))

ax1.semilogy(n_tsp, t_gr, "o-", color=C_GREEDY, lw=2.2,
             markersize=7, label="Greedy — Vecino más cercano (medido)")
ax1.semilogy(n_tsp, t_hk, "s-", color=C_HK, lw=2.2,
             markersize=7, label="Held-Karp — TSP exacto (medido)")
ax1.semilogy(n_ref, ref_gr, "--", color=C_GREEDY, lw=1.2, alpha=0.55,
             label=r"Referencia $O(n^2)$")
ax1.semilogy(n_ref, ref_hk, "--", color=C_HK, lw=1.2, alpha=0.55,
             label=r"Referencia $O(2^n \cdot n^2)$")

ax1.set_xlabel("Número de pedidos activos (n)")
ax1.set_ylabel("Tiempo de ejecución (ms) — escala log")
ax1.set_title("Figura 1. Tiempo de ejecución: Greedy vs Held-Karp (TSP)")
ax1.set_xticks(n_tsp)
ax1.grid(True, which="both", linestyle=":", alpha=GRID_ALPHA)
ax1.legend(framealpha=0.9, loc="upper left")

# Anotar el último punto HK para contexto
ax1.annotate(
    f"{t_hk[-1]:.1f} ms (n={n_tsp[-1]})",
    xy=(n_tsp[-1], t_hk[-1]),
    xytext=(n_tsp[-1] - 2.2, t_hk[-1] * 3.5),
    arrowprops=dict(arrowstyle="->", color=C_HK),
    color=C_HK, fontsize=9,
)

fig1.tight_layout()
out1 = FIGURAS_DIR / "fig1_tiempo_vs_n.png"
fig1.savefig(out1, dpi=300, bbox_inches="tight")
plt.close(fig1)
print(f"[OK] {out1}")

# ══════════════════════════════════════════════════════════════════════════════
# FIGURA 2 — Calidad de ruta: Distancia Greedy vs Held-Karp + Gap %
# ══════════════════════════════════════════════════════════════════════════════
d_gr  = [v / 1000 for v in tsp["distancia_greedy_m"]]     # km
d_hk  = [v / 1000 for v in tsp["distancia_held_karp_m"]]  # km
gap   = tsp["gap_porcentaje"]

fig2, (ax2a, ax2b) = plt.subplots(1, 2, figsize=(11, 4.8))

# — Panel izquierdo: barras agrupadas
x     = np.arange(len(n_tsp))
width = 0.35
bars_hk = ax2a.bar(x - width/2, d_hk, width, label="Held-Karp (óptimo)",
                   color=C_HK, alpha=0.88, edgecolor="white")
bars_gr = ax2a.bar(x + width/2, d_gr, width, label="Greedy (heurística)",
                   color=C_GREEDY, alpha=0.88, edgecolor="white")

ax2a.set_xticks(x)
ax2a.set_xticklabels([f"n={v}" for v in n_tsp])
ax2a.set_ylabel("Distancia total de ruta (km)")
ax2a.set_title("Calidad de solución: distancia total")
ax2a.legend()
ax2a.grid(axis="y", linestyle=":", alpha=GRID_ALPHA)
ax2a.set_ylim(0, max(d_gr) * 1.18)

# Etiquetas en barras
for bar in bars_hk:
    h = bar.get_height()
    ax2a.text(bar.get_x() + bar.get_width()/2, h + 0.03,
              f"{h:.2f}", ha="center", va="bottom", fontsize=8, color=C_HK)
for bar in bars_gr:
    h = bar.get_height()
    ax2a.text(bar.get_x() + bar.get_width()/2, h + 0.03,
              f"{h:.2f}", ha="center", va="bottom", fontsize=8, color=C_GREEDY)

# — Panel derecho: gap porcentual
colors_gap = [C_GREEDY if g == 0 else C_HK for g in gap]
bars_gap = ax2b.bar(x, gap, color=colors_gap, alpha=0.82, edgecolor="white")
ax2b.set_xticks(x)
ax2b.set_xticklabels([f"n={v}" for v in n_tsp])
ax2b.set_ylabel("Gap de calidad (%)")
ax2b.set_title("Suboptimalidad del Greedy vs óptimo HK")
ax2b.grid(axis="y", linestyle=":", alpha=GRID_ALPHA)
ax2b.set_ylim(0, max(gap) * 1.25)

for bar, g_val in zip(bars_gap, gap):
    ax2b.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
              f"{g_val:.1f}%", ha="center", va="bottom", fontsize=9)

fig2.suptitle("Figura 2. Comparación de calidad de ruta: Greedy vs Held-Karp",
              fontsize=13, fontweight="bold")
fig2.tight_layout()
out2 = FIGURAS_DIR / "fig2_calidad_ruta.png"
fig2.savefig(out2, dpi=300, bbox_inches="tight")
plt.close(fig2)
print(f"[OK] {out2}")

# ══════════════════════════════════════════════════════════════════════════════
# FIGURA 3 — Backtracking: rutas encontradas, ramas podadas, estados visitados
# ══════════════════════════════════════════════════════════════════════════════
bt_casos    = data["backtracking"]["casos_backtracking"]
descrips    = [c["descripcion"].split("(")[1].rstrip(")") for c in bt_casos]
rutas_enc   = [c["rutas_encontradas"]    for c in bt_casos]
ramas_pod   = [c["ramas_podadas"]         for c in bt_casos]
estados_vis = [c["estados_visitados"]     for c in bt_casos]
tiempos_bt  = [c["tiempo_ms"]             for c in bt_casos]

x3    = np.arange(len(bt_casos))
width = 0.28

fig3, (ax3a, ax3b) = plt.subplots(1, 2, figsize=(12, 5))

# — Panel izquierdo: barras agrupadas (ramas y estados)
b_ramas = ax3a.bar(x3 - width/2, ramas_pod, width, label="Ramas podadas",
                   color=C_BT_RAMAS, alpha=0.85)
b_estad = ax3a.bar(x3 + width/2, estados_vis, width, label="Estados visitados",
                   color=C_BT_EST, alpha=0.85)
ax3a.set_xticks(x3)
ax3a.set_xticklabels(descrips, fontsize=9)
ax3a.set_ylabel("Cantidad")
ax3a.set_title("Efectividad de la poda en Backtracking")
ax3a.legend()
ax3a.grid(axis="y", linestyle=":", alpha=GRID_ALPHA)

for bar in b_ramas:
    h = bar.get_height()
    ax3a.text(bar.get_x() + bar.get_width()/2, h + 3,
              str(int(h)), ha="center", va="bottom", fontsize=8)
for bar in b_estad:
    h = bar.get_height()
    ax3a.text(bar.get_x() + bar.get_width()/2, h + 3,
              str(int(h)), ha="center", va="bottom", fontsize=8)

# — Panel derecho: rutas encontradas y tiempo de ejecución en eje secundario
ax3b_twin = ax3b.twinx()
b_rutas = ax3b.bar(x3, rutas_enc, 0.5, color=C_BT_RUTAS, alpha=0.80,
                   label="Rutas encontradas")
line_t  = ax3b_twin.plot(x3, tiempos_bt, "D--", color="#333333", lw=1.8,
                         markersize=7, label="Tiempo (ms)")
ax3b.set_xticks(x3)
ax3b.set_xticklabels(descrips, fontsize=9)
ax3b.set_ylabel("Rutas alternativas encontradas")
ax3b_twin.set_ylabel("Tiempo de ejecución (ms)")
ax3b.set_title("Rutas encontradas y tiempo de cómputo")
ax3b.set_ylim(0, max(rutas_enc) * 1.5)
ax3b_twin.set_ylim(0, max(tiempos_bt) * 1.6)

# Combinar leyendas
handles1, labels1 = ax3b.get_legend_handles_labels()
handles2, labels2 = ax3b_twin.get_legend_handles_labels()
ax3b.legend(handles1 + handles2, labels1 + labels2, loc="upper left", fontsize=9)
ax3b.grid(axis="y", linestyle=":", alpha=GRID_ALPHA)

for bar, rv in zip(b_rutas, rutas_enc):
    ax3b.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
              str(rv), ha="center", va="bottom", fontsize=9, fontweight="bold")

fig3.suptitle("Figura 3. Rendimiento del algoritmo Backtracking con poda",
              fontsize=13, fontweight="bold")
fig3.tight_layout()
out3 = FIGURAS_DIR / "fig3_backtracking.png"
fig3.savefig(out3, dpi=300, bbox_inches="tight")
plt.close(fig3)
print(f"[OK] {out3}")

print("\nTodas las figuras generadas exitosamente en:", FIGURAS_DIR)
