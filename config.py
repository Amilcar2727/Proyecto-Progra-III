"""
Módulo de Configuración Global del Sistema de Rutas Cusco.
Contiene parámetros de mapas, constantes visuales y umbrales algorítmicos.
"""

from pathlib import Path

# Rutas base del proyecto
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

NODOS_FILE = DATA_DIR / "nodos_cusco.json"
PEDIDOS_FILE = DATA_DIR / "pedidos.json"
REPARTIDORES_FILE = DATA_DIR / "repartidores.json"
RED_VIAL_CACHE_FILE = DATA_DIR / "red_vial_cache.json"

# Construcción offline de la red de interés a partir de OSM.
RESPETAR_SENTIDOS = True
K_VECINOS = 3

# Configuración del Mapa
# Centro inicial en la Plaza de Armas de Cusco
MAPA_CENTRO_LAT = -13.5167
MAPA_CENTRO_LON = -71.9788
MAPA_ZOOM_INICIAL = 14

# Proveedores de Tiles:
# OpenStreetMap (por defecto, libre y oficial)
TILES_OPENSTREETMAP = "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"

# NOTA: Los tiles de Google Maps son para demostración académica.
# Su uso directo sin API Key comercial puede infringir los Términos de Servicio de Google.
TILES_GOOGLE_NORMAL = "https://mt0.google.com/vt/lyrs=m&hl=es&x={x}&y={y}&z={z}"
TILES_GOOGLE_SATELITE = "https://mt0.google.com/vt/lyrs=s&hl=es&x={x}&y={y}&z={z}"

# Proveedor activo por defecto
TILE_PROVIDER_ACTUAL = TILES_OPENSTREETMAP
MAX_ZOOM = 19
MIN_ZOOM = 10

# Paleta de Colores para Visualización
COLOR_NODO_DEFECTO = "#1f2937"        # Gris oscuro
COLOR_NODO_SELECCIONADO = "#2563eb"   # Azul vibrante
COLOR_CALLE_NORMAL = "#9ca3af"        # Gris tenue
COLOR_CALLE_BLOQUEADA = "#dc2626"     # Rojo intenso
COLOR_RUTA_GREEDY = "#059669"         # Verde esmeralda
COLOR_RUTA_HELD_KARP = "#7c3aed"     # Púrpura
COLOR_RUTA_BACKTRACKING = "#d97706"  # Ámbar
COLOR_RUTA_OPTIMA = "#e11d48"         # Rosa rojizo brillante
COLOR_REPARTIDOR = "#0284c7"          # Celeste

# Colores para Zonas de Divide y Vencerás
COLORES_ZONAS = [
    "#3b82f6",  # Azul
    "#10b981",  # Verde
    "#f59e0b",  # Ámbar
    "#ec4899",  # Rosa
    "#8b5cf6",  # Violeta
    "#06b6d4",  # Cian
    "#84cc16",  # Lima
    "#f97316",  # Naranja
]

# Umbrales y límites de seguridad algorítmica
LIMITE_HELD_KARP_N = 12       # N máximo antes de advertir O(n^2 2^n)
LIMITE_BACKTRACKING_RUTAS = 500  # Poda de seguridad para no saturar memoria
TIMEOUT_BACKTRACKING_SEG = 5.0   # Segundos máximos antes de corte en GUI
UMBRAL_DYV_K = 5              # Tamaño máximo de subproblema en Divide y Vencerás
