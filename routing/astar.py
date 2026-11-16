"""A* implementado desde cero sobre el grafo de OSMnx.

Solo se usa networkx como estructura de datos (nodos, vecinos, atributos de
aristas). La búsqueda, la cola de prioridad y la heurística son propias.
"""

import heapq
import math
from itertools import count

EARTH_RADIUS_M = 6_371_000


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia en metros sobre la superficie de la Tierra (línea recta 'en el aire')."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def edge_cost(G, u, v, weight: str) -> float:
    """Costo de ir de u a v. En un MultiDiGraph puede haber varias aristas
    paralelas u->v (keys 0, 1, ...): se toma la más barata."""
    return min(float(data[weight]) for data in G[u][v].values())


def max_speed_mps(G) -> float:
    """Velocidad máxima del grafo en m/s. Se usa para que la heurística de
    tiempo nunca sobreestime."""
    max_kph = max(float(data["speed_kph"]) for _, _, data in G.edges(data=True))
    return max_kph / 3.6


def astar(G, source, target, weight: str = "length", heuristic: bool = True, v_max_mps: float | None = None):
    """Busca el camino de menor costo entre source y target.

    weight:    "length" (metros) o "travel_time" (segundos).
    heuristic: False convierte el algoritmo en Dijkstra (h = 0). Sirve para comparar.
    v_max_mps: velocidad máxima del grafo; si no se pasa, se calcula (es lento,
               conviene calcularla una vez y reutilizarla).

    Devuelve (path, cost, nodes_expanded).
    Lanza ValueError si no hay camino.
    """
    if weight == "travel_time" and heuristic and v_max_mps is None:
        v_max_mps = max_speed_mps(G)

    t_lat, t_lon = G.nodes[target]["y"], G.nodes[target]["x"]

    def h(n) -> float:
        if not heuristic:
            return 0.0
        d = haversine_m(G.nodes[n]["y"], G.nodes[n]["x"], t_lat, t_lon)
        if weight == "length":
            return d
        return d / v_max_mps

    tie = count()
    open_heap = [(h(source), next(tie), source)]
    g = {source: 0.0}
    came_from = {}
    closed = set()
    nodes_expanded = 0

    while open_heap:
        _, _, u = heapq.heappop(open_heap)

        if u in closed:
            continue
        if u == target:
            return _rebuild(came_from, target), g[target], nodes_expanded

        closed.add(u)
        nodes_expanded += 1

        for v in G.neighbors(u):
            if v in closed:
                continue
            tentative = g[u] + edge_cost(G, u, v, weight)
            if tentative < g.get(v, math.inf):
                g[v] = tentative
                came_from[v] = u
                heapq.heappush(open_heap, (tentative + h(v), next(tie), v))

    raise ValueError(f"No hay camino entre {source} y {target}")


def _rebuild(came_from: dict, node) -> list:
    path = [node]
    while node in came_from:
        node = came_from[node]
        path.append(node)
    path.reverse()
    return path