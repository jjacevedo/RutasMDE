"""Descarga el grafo vial de Medellín desde OpenStreetMap y lo deja listo para A*.

Uso (desde la raíz del repo):
    python routing/download_graph.py

"""

from pathlib import Path

import osmnx as ox

PLACES = [
    "Medellín, Antioquia, Colombia",
    "Envigado, Antioquia, Colombia",
    "Itagüí, Antioquia, Colombia",
    "Bello, Antioquia, Colombia",
]
NETWORK_TYPE = "drive"
OUTPUT = Path(__file__).resolve().parent / "data" / "medellin.graphml"

OVERPASS_SERVERS = [
    "https://overpass-api.de/api",
    "https://overpass.kumi.systems/api",
    "https://maps.mail.ru/osm/tools/overpass/api",
]


def with_overpass_fallback(fn, *args, **kwargs):
    """Ejecuta fn (p. ej. ox.graph_from_place) probando cada servidor Overpass hasta que uno responda."""
    ox.settings.requests_timeout = 300
    last_error = None
    for url in OVERPASS_SERVERS:
        ox.settings.overpass_url = url
        ox.settings.overpass_rate_limit = url == OVERPASS_SERVERS[0]
        print(f"  Probando servidor {url} ...")
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            print(f"  Falló ({type(e).__name__}). Probando el siguiente...")
            last_error = e
    raise RuntimeError("Ningún servidor Overpass respondió. Revisa tu conexión o prueba en otra red.") from last_error


def main() -> None:
    print(f"Descargando grafo de {len(PLACES)} municipios (network_type={NETWORK_TYPE})...")
    G = with_overpass_fallback(ox.graph_from_place, PLACES, network_type=NETWORK_TYPE)
    print(f"  Descargado: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")

    G = ox.truncate.largest_component(G, strongly=True)
    print(f"  Componente fuertemente conexa: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")

    G = ox.routing.add_edge_speeds(G)
    G = ox.routing.add_edge_travel_times(G)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    ox.save_graphml(G, OUTPUT)
    size_mb = OUTPUT.stat().st_size / 1e6
    print(f"Grafo guardado en {OUTPUT} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()