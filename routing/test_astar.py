"""Valida el A* propio y lo compara con Dijkstra.

Uso (desde la raíz del repo, con el grafo ya descargado):
    python -m routing.test_astar

1) Correctitud: el costo de nuestro A* debe ser igual al de networkx
   (networkx solo se usa como referencia, no para calcular rutas).
2) Eficiencia: nodos expandidos por A* vs. Dijkstra (nuestro A* con h = 0).
"""

import random
import time
from pathlib import Path

import networkx as nx

from routing.astar import astar, max_speed_mps

N_PAIRS = 15
SEED = 42
RESULTS_PATH = Path(__file__).resolve().parent / "data" / "resultados_astar.txt"


def validate(G, n_pairs: int = N_PAIRS, seed: int = SEED) -> list[dict]:
    rng = random.Random(seed)
    nodes = list(G.nodes)
    v_max = max_speed_mps(G)
    rows = []

    for weight in ("length", "travel_time"):
        for _ in range(n_pairs):
            s, t = rng.sample(nodes, 2)

            t0 = time.perf_counter()
            _, cost_a, exp_a = astar(G, s, t, weight=weight, v_max_mps=v_max)
            ms_a = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            _, cost_d, exp_d = astar(G, s, t, weight=weight, heuristic=False)
            ms_d = (time.perf_counter() - t0) * 1000

            ref = nx.shortest_path_length(G, s, t, weight=weight)
            ok = abs(cost_a - ref) < 1e-6 and abs(cost_d - ref) < 1e-6
            rows.append(dict(weight=weight, cost=cost_a, ref=ref, ok=ok,
                             exp_astar=exp_a, exp_dijkstra=exp_d, ms_astar=ms_a, ms_dijkstra=ms_d))
    return rows


def report(rows: list[dict]) -> str:
    lines = []
    for weight in ("length", "travel_time"):
        sub = [r for r in rows if r["weight"] == weight]
        n_ok = sum(r["ok"] for r in sub)
        exp_a = sum(r["exp_astar"] for r in sub) / len(sub)
        exp_d = sum(r["exp_dijkstra"] for r in sub) / len(sub)
        ms_a = sum(r["ms_astar"] for r in sub) / len(sub)
        ms_d = sum(r["ms_dijkstra"] for r in sub) / len(sub)
        lines.append(f"\nPeso = {weight}")
        lines.append(f"  Rutas óptimas (igual a networkx): {n_ok}/{len(sub)}")
        lines.append(f"  Nodos expandidos promedio  A*: {exp_a:8.0f} | Dijkstra: {exp_d:8.0f} "
                     f"| A* expande {100 * exp_a / exp_d:.0f}% de lo que expande Dijkstra")
        lines.append(f"  Tiempo promedio (ms)       A*: {ms_a:8.1f} | Dijkstra: {ms_d:8.1f}")
        for r in sub:
            if not r["ok"]:
                lines.append(f"  ERROR: costo A*={r['cost']:.3f} vs networkx={r['ref']:.3f}")
    return "\n".join(lines)


if __name__ == "__main__":
    from routing.router import load_graph

    G = load_graph()
    text = f"Grafo: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas\n" + report(validate(G))
    print(text)
    RESULTS_PATH.write_text(text + "\n", encoding="utf-8")
    print(f"\nResultados guardados en {RESULTS_PATH}")