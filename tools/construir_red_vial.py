"""Construye un grafo disperso de lugares de interés con rutas reales de OSM.

Requiere dependencias de desarrollo: pip install -r requirements-dev.txt
La descarga de OSM se realiza únicamente al ejecutar este script.
"""

from __future__ import annotations

import inspect
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import networkx as nx
import osmnx as ox
from pyproj import Transformer
from shapely.geometry import LineString

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config  # noqa: E402


NODOS_FILE = ROOT / "data" / "nodos_cusco.json"
OUTPUT_FILE = config.RED_VIAL_CACHE_FILE
NETWORK_TYPE = "drive"
MARGEN_M = 1300.0
DISTANCIA_MAX_AJUSTE_M = 60.0
TOLERANCIA_SIMPLIFICACION_M = 4.0
ATRIBUCION = "© OpenStreetMap contributors (ODbL)"


def _bbox_con_margen(nodos: list[dict[str, Any]]) -> tuple[float, float, float, float]:
    """Devuelve (west, south, east, north) con un margen métrico aproximado."""
    latitudes = [float(nodo["lat"]) for nodo in nodos]
    longitudes = [float(nodo["lon"]) for nodo in nodos]
    lat_centro = (min(latitudes) + max(latitudes)) / 2.0
    margen_lat = MARGEN_M / 111_320.0
    margen_lon = MARGEN_M / (111_320.0 * math.cos(math.radians(lat_centro)))
    return (
        min(longitudes) - margen_lon,
        min(latitudes) - margen_lat,
        max(longitudes) + margen_lon,
        max(latitudes) + margen_lat,
    )


def _descargar_grafo(bbox: tuple[float, float, float, float]):
    """Llama a graph_from_bbox con la firma compatible con OSMnx instalado."""
    funcion = getattr(ox, "graph_from_bbox", None)
    if funcion is None:
        funcion = ox.graph.graph_from_bbox
    parametros = inspect.signature(funcion).parameters
    if "bbox" in parametros:
        return funcion(
            bbox=bbox,
            network_type=NETWORK_TYPE,
            simplify=True,
            retain_all=True,
        )

    west, south, east, north = bbox
    return funcion(
        north=north,
        south=south,
        east=east,
        west=west,
        network_type=NETWORK_TYPE,
        simplify=True,
        retain_all=True,
    )


def _mayor_componente_fuertemente_conexa(grafo):
    componentes = nx.strongly_connected_components(grafo)
    mayor = max(componentes, key=len, default=set())
    if not mayor:
        raise RuntimeError("OSM no devolvió una componente vial fuertemente conexa.")
    return grafo.subgraph(mayor).copy()


def _distancia_ajuste_m(grafo, nodo_osm: Any, lat: float, lon: float) -> float:
    attrs = grafo.nodes[nodo_osm]
    return float(ox.distance.great_circle(
        lat, lon, float(attrs["y"]), float(attrs["x"])
    ))


def _camino_mas_corto(grafo, origen: Any, destino: Any):
    return nx.shortest_path(grafo, origen, destino, weight="length", method="dijkstra")


def _arista_osm_minima(grafo, origen: Any, destino: Any) -> dict[str, Any]:
    """Selecciona el tramo paralelo de menor longitud para un par de nodos OSM."""
    alternativas = grafo.get_edge_data(origen, destino)
    if not alternativas:
        raise RuntimeError(f"No existe tramo OSM dirigido entre {origen} y {destino}.")
    return min(alternativas.values(), key=lambda attrs: float(attrs.get("length", 0.0)))


def _nombres_via(valor: Any) -> list[str]:
    if valor is None:
        return []
    valores = valor if isinstance(valor, (list, tuple, set)) else [valor]
    return list(dict.fromkeys(str(nombre) for nombre in valores if nombre))


def _ruta_osm(grafo, camino: list[Any]) -> tuple[float, list[list[float]], list[str]]:
    longitud_total = 0.0
    puntos_lonlat: list[tuple[float, float]] = []
    calles: list[str] = []

    for origen, destino in zip(camino, camino[1:]):
        attrs = _arista_osm_minima(grafo, origen, destino)
        longitud_total += float(attrs.get("length", 0.0))
        calles.extend(nombre for nombre in _nombres_via(attrs.get("name")) if nombre not in calles)

        geometry = attrs.get("geometry")
        if geometry is not None:
            coords = list(geometry.coords)
        else:
            coords = [
                (float(grafo.nodes[origen]["x"]), float(grafo.nodes[origen]["y"])),
                (float(grafo.nodes[destino]["x"]), float(grafo.nodes[destino]["y"])),
            ]

        inicio = (float(grafo.nodes[origen]["x"]), float(grafo.nodes[origen]["y"]))
        final = (float(grafo.nodes[destino]["x"]), float(grafo.nodes[destino]["y"]))
        if math.dist(coords[0], inicio) > math.dist(coords[-1], inicio):
            coords.reverse()

        if puntos_lonlat and coords and puntos_lonlat[-1] == coords[0]:
            puntos_lonlat.extend(coords[1:])
        else:
            puntos_lonlat.extend(coords)

    if len(puntos_lonlat) < 2:
        raise RuntimeError("El camino OSM no produjo una polilínea válida.")

    linea = LineString(puntos_lonlat)
    centro_lon = sum(p[0] for p in puntos_lonlat) / len(puntos_lonlat)
    zona_utm = int((centro_lon + 180.0) // 6.0) + 1
    epsg_utm = (32700 if sum(p[1] for p in puntos_lonlat) < 0 else 32600) + zona_utm
    hacia_utm = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg_utm}", always_xy=True)
    hacia_wgs84 = Transformer.from_crs(f"EPSG:{epsg_utm}", "EPSG:4326", always_xy=True)
    linea_utm = LineString([hacia_utm.transform(lon, lat) for lon, lat in linea.coords])
    simplificada = linea_utm.simplify(
        TOLERANCIA_SIMPLIFICACION_M, preserve_topology=False
    )
    geometria = [
        [float(lat), float(lon)]
        for lon, lat in (hacia_wgs84.transform(x, y) for x, y in simplificada.coords)
    ]
    return longitud_total, geometria, calles


def _formar_arista(
    grafo_osm,
    nodos_osm: dict[str, Any],
    origen_id: str,
    destino_id: str,
) -> dict[str, Any] | None:
    origen_osm = nodos_osm[origen_id]
    destino_osm = nodos_osm[destino_id]
    camino = _camino_mas_corto(grafo_osm, origen_osm, destino_osm)
    ids_interes = set(nodos_osm.values())
    if any(nodo in ids_interes for nodo in camino[1:-1]):
        return None
    longitud, geometria, calles = _ruta_osm(grafo_osm, camino)
    return {
        "origen": origen_id,
        "destino": destino_id,
        "longitud_m": longitud,
        "geometria": geometria,
        "calles": calles,
    }


def _construir_aristas(
    grafo_osm, nodos_osm: dict[str, Any]
) -> tuple[list[dict], int, int, dict[tuple[str, str], dict[str, Any]]]:
    ids = list(nodos_osm)
    candidatos: dict[tuple[str, str], dict[str, Any]] = {}
    distancias: dict[str, list[tuple[float, str]]] = {}

    for origen_id in ids:
        destinos = []
        for destino_id in ids:
            if destino_id == origen_id:
                continue
            arista = _formar_arista(grafo_osm, nodos_osm, origen_id, destino_id)
            if arista is None:
                continue
            candidatos[(origen_id, destino_id)] = arista
            destinos.append((arista["longitud_m"], destino_id))
        distancias[origen_id] = sorted(destinos)

    if not candidatos:
        raise RuntimeError("No se encontró ninguna conexión elegible entre lugares de interés.")

    k = max(1, min(int(config.K_VECINOS), len(ids) - 1))
    seleccionadas = {}
    for origen_id in ids:
        for _, destino_id in distancias[origen_id][:k]:
            seleccionadas[(origen_id, destino_id)] = candidatos[(origen_id, destino_id)]

    grafo_interes = nx.DiGraph()
    grafo_interes.add_nodes_from(ids)
    grafo_interes.add_edges_from(seleccionadas)
    if nx.is_strongly_connected(grafo_interes):
        return list(seleccionadas.values()), k, 0, candidatos

    grafo_candidatos = nx.DiGraph()
    grafo_candidatos.add_nodes_from(ids)
    grafo_candidatos.add_weighted_edges_from(
        (origen, destino, arista["longitud_m"])
        for (origen, destino), arista in candidatos.items()
    )
    if not nx.is_strongly_connected(grafo_candidatos):
        raise RuntimeError(
            "Las conexiones elegibles no forman un grafo fuertemente conexo. "
            "Revise los snaps y las rutas OSM que atraviesan lugares intermedios."
        )

    mejor_solucion = None
    for inicio in ids:
        aristas_conectoras = set()
        visitados = {inicio}
        actual = inicio
        while len(visitados) < len(ids):
            opciones = []
            for destino in ids:
                if destino in visitados:
                    continue
                camino = nx.shortest_path(
                    grafo_candidatos, actual, destino, weight="weight"
                )
                costo = sum(
                    grafo_candidatos[a][b]["weight"]
                    for a, b in zip(camino, camino[1:])
                )
                opciones.append((costo, destino, camino))
            _, _, camino = min(opciones)
            aristas_conectoras.update(zip(camino, camino[1:]))
            visitados.update(camino)
            actual = camino[-1]

        camino_cierre = nx.shortest_path(
            grafo_candidatos, actual, inicio, weight="weight"
        )
        aristas_conectoras.update(zip(camino_cierre, camino_cierre[1:]))
        solucion = dict(seleccionadas)
        for par in aristas_conectoras:
            solucion[par] = candidatos[par]

        comprobacion = nx.DiGraph()
        comprobacion.add_nodes_from(ids)
        comprobacion.add_edges_from(solucion)
        grados = [comprobacion.out_degree(nodo_id) for nodo_id in ids]
        if not nx.is_strongly_connected(comprobacion):
            continue
        puntuacion = (
            sum(grado > 4 for grado in grados),
            max(grados),
            len(solucion),
            ids.index(inicio),
        )
        if mejor_solucion is None or puntuacion < mejor_solucion[0]:
            mejor_solucion = (puntuacion, solucion)

    if mejor_solucion is None:
        raise RuntimeError("No fue posible reparar la conexidad del grafo disperso.")
    resultado = mejor_solucion[1]
    return (
        list(resultado.values()),
        k,
        len(set(resultado) - set(seleccionadas)),
        candidatos,
    )


def _simetrizar(
    aristas: list[dict[str, Any]],
    candidatos: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    pares = []
    vistos = set()
    for arista in aristas:
        par = tuple(sorted((arista["origen"], arista["destino"])))
        if par not in vistos:
            vistos.add(par)
            pares.append(par)

    simetricas = []
    for a, b in pares:
        opciones = [
            candidatos[(origen, destino)]
            for origen, destino in ((a, b), (b, a))
            if (origen, destino) in candidatos
        ]
        elegida = min(opciones, key=lambda arista: arista["longitud_m"])
        geometria = elegida["geometria"]
        simetricas.append({**elegida, "origen": a, "destino": b})
        simetricas.append({
            **elegida,
            "origen": b,
            "destino": a,
            "geometria": list(reversed(geometria)),
        })
    return simetricas


def construir() -> dict[str, Any]:
    with NODOS_FILE.open(encoding="utf-8") as archivo:
        datos = json.load(archivo)
    nodos = datos.get("nodos", [])
    if not nodos:
        raise ValueError(f"No hay nodos de interés en {NODOS_FILE}.")

    bbox = _bbox_con_margen(nodos)
    ox.settings.use_cache = False
    print(f"OSMnx {ox.__version__}; descargando red {NETWORK_TYPE} para bbox {bbox}...")
    grafo_osm = _mayor_componente_fuertemente_conexa(_descargar_grafo(bbox))
    print(
        f"Componente vial fuertemente conexa: {len(grafo_osm.nodes):,} nodos, "
        f"{len(grafo_osm.edges):,} tramos."
    )

    snaps: dict[str, Any] = {}
    nodos_cache = []
    avisos = []
    for nodo in nodos:
        lat, lon = float(nodo["lat"]), float(nodo["lon"])
        id_osm = ox.distance.nearest_nodes(grafo_osm, X=lon, Y=lat)
        attrs = grafo_osm.nodes[id_osm]
        distancia = _distancia_ajuste_m(grafo_osm, id_osm, lat, lon)
        snaps[nodo["id"]] = id_osm
        nodos_cache.append({
            "id": nodo["id"],
            "nombre": nodo["nombre"],
            "sector": nodo.get("sector", ""),
            "lat_original": lat,
            "lon_original": lon,
            "lat_ajustado": float(attrs["y"]),
            "lon_ajustado": float(attrs["x"]),
            "id_osm": str(id_osm),
            "distancia_ajuste_m": distancia,
        })
        if distancia > DISTANCIA_MAX_AJUSTE_M:
            avisos.append(
                f"AJUSTE > {DISTANCIA_MAX_AJUSTE_M:.0f} m: {nodo['id']} {nodo['nombre']} "
                f"({distancia:.1f} m). Coordenada propuesta: "
                f"lat={float(attrs['y']):.7f}, lon={float(attrs['x']):.7f}."
            )

    por_osm: dict[Any, list[str]] = {}
    for nodo_id, id_osm in snaps.items():
        por_osm.setdefault(id_osm, []).append(nodo_id)
    for id_osm, ids in por_osm.items():
        if len(ids) > 1:
            attrs = grafo_osm.nodes[id_osm]
            avisos.append(
                f"SNAP DUPLICADO: {', '.join(ids)} comparten OSM {id_osm}. "
                f"Coordenada propuesta común: lat={float(attrs['y']):.7f}, "
                f"lon={float(attrs['x']):.7f}; revise y ajuste manualmente los lugares."
            )

    if avisos:
        print("\nREVISIÓN MANUAL DE COORDENADAS:")
        for aviso in avisos:
            print(f"  - {aviso}")

    aristas, k_usado, aristas_conectividad, candidatos = _construir_aristas(
        grafo_osm, snaps
    )
    if not config.RESPETAR_SENTIDOS:
        aristas = _simetrizar(aristas, candidatos)

    resultado = {
        "nodos": nodos_cache,
        "aristas": aristas,
        "metadatos": {
            "fecha_descarga_utc": datetime.now(timezone.utc).isoformat(),
            "version_osmnx": ox.__version__,
            "bbox": {
                "west": bbox[0],
                "south": bbox[1],
                "east": bbox[2],
                "north": bbox[3],
            },
            "network_type": NETWORK_TYPE,
            "respetar_sentidos": bool(config.RESPETAR_SENTIDOS),
            "k_configurado": int(config.K_VECINOS),
            "k_usado": k_usado,
            "aristas_conectividad_adicionales": aristas_conectividad,
            "atribucion": ATRIBUCION,
            "avisos_coordenadas": avisos,
        },
    }
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as archivo:
        json.dump(resultado, archivo, ensure_ascii=False, indent=2)
    print(
        f"Cache escrito: {OUTPUT_FILE} ({len(nodos_cache)} lugares, "
        f"{len(aristas)} aristas; k={k_usado})."
    )
    return resultado


if __name__ == "__main__":
    try:
        construir()
    except Exception as error:
        raise SystemExit(
            f"No se pudo construir el cache vial: {error}\n"
            "Compruebe la conexión a Overpass y vuelva a ejecutar "
            "`python tools/construir_red_vial.py`."
        ) from error
