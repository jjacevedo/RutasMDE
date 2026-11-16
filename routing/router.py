"""Función pública del Rol B: compute_route().

Prueba rápida (desde la raíz del repo):
    python -c "from routing.router import compute_route; print(compute_route('EAFIT', 'Parque Berrío'))"
"""

from functools import lru_cache
from pathlib import Path

import osmnx as ox

from routing.astar import astar, max_speed_mps
from routing.geocoding import geocode_with_name, nearest_node

GRAPH_PATH = Path(__file__).resolve().parent / "data" / "medellin.graphml"

WEIGHTS = {"distance": "length", "time": "travel_time"}


@lru_cache(maxsize=1)
def load_graph():
    """Carga el grafo UNA sola vez por proceso (leer el .graphml toma varios segundos)."""
    if not GRAPH_PATH.exists():
        raise FileNotFoundError(f"No existe {GRAPH_PATH}. Corre primero: python routing/download_graph.py")
    return ox.load_graphml(GRAPH_PATH)


@lru_cache(maxsize=1)
def _v_max() -> float:
    return max_speed_mps(load_graph())


def _best_edge(G, u, v, attr: str) -> dict:
    """Datos de la arista u->v más barata (puede haber paralelas)."""
    return min(G[u][v].values(), key=lambda d: float(d[attr]))


def _sq_dist(a, b) -> float:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def _path_to_coords_and_totals(G, path: list, attr: str):
    """Convierte la lista de nodos en coordenadas (lat, lon) y suma metros y segundos.

    Si la arista trae 'geometry' (la forma real de la calle curva), se usan esos
    puntos; así la línea en el mapa sigue la calle en vez de cortar en diagonal.
    """
    coords = [(G.nodes[path[0]]["y"], G.nodes[path[0]]["x"])]
    meters = seconds = 0.0
    for u, v in zip(path[:-1], path[1:]):
        data = _best_edge(G, u, v, attr)
        meters += float(data["length"])
        seconds += float(data["travel_time"])
        if "geometry" in data:
            pts = [(lat, lon) for lon, lat in data["geometry"].coords]
            here = coords[-1]
            if _sq_dist(pts[-1], here) < _sq_dist(pts[0], here):
                pts.reverse()
            coords.extend(pts[1:])
        else:
            coords.append((G.nodes[v]["y"], G.nodes[v]["x"]))
    return coords, meters, seconds


def compute_route(origin: str, destination: str, weight: str = "distance") -> dict:
    if weight not in WEIGHTS:
        raise ValueError(f"weight debe ser 'distance' o 'time', no '{weight}'")
    attr = WEIGHTS[weight]
    G = load_graph()

    o_lat, o_lon, o_name = geocode_with_name(origin)
    d_lat, d_lon, d_name = geocode_with_name(destination)
    source = nearest_node(G, o_lat, o_lon)
    target = nearest_node(G, d_lat, d_lon)

    if source == target:
        path, nodes_expanded = [source], 0
    else:
        path, _, nodes_expanded = astar(G, source, target, weight=attr, v_max_mps=_v_max())

    coords, meters, seconds = _path_to_coords_and_totals(G, path, attr)

    return {
        "coords": [(round(lat, 6), round(lon, 6)) for lat, lon in coords],
        "origin_coords": (round(o_lat, 6), round(o_lon, 6)),
        "dest_coords": (round(d_lat, 6), round(d_lon, 6)),
        "distance_km": round(meters / 1000, 2),
        "time_min": round(seconds / 60, 1),
        "nodes_expanded": nodes_expanded,
        "origin_name": o_name,
        "dest_name": d_name,
    }