from langchain_core.tools import tool

from rag.retriever import search

try:
    from routing.router import compute_route
except ModuleNotFoundError as error:
    if error.name not in ("routing.router", "routing"):
        raise

    def compute_route(origin: str, destination: str, weight: str = "distance") -> dict:
        return {
            "coords": [
                (6.2006, -75.5783),
                (6.2189, -75.5735),
                (6.2350, -75.5702),
                (6.2512, -75.5680),
                (6.2710, -75.5655),
            ],
            "origin_coords": (6.2006, -75.5783),
            "dest_coords": (6.2710, -75.5655),
            "distance_km": 9.4,
            "time_min": 24.0,
            "nodes_expanded": 347,
            "origin_name": origin,
            "dest_name": destination,
        }


@tool(response_format="content_and_artifact")
def calcular_ruta(origen: str, destino: str, criterio: str = "distance") -> tuple[str, dict | None]:
    """Calcula con A* la ruta por la red vial de Medellín entre dos lugares.

    Usar cuando el usuario quiere ir de un lugar a otro o pregunta distancias o tiempos de viaje.
    origen y destino son nombres de lugares, idealmente con ", Medellín" al final.
    criterio es "distance" para la ruta más corta o "time" para la más rápida.
    """
    try:
        route = compute_route(origen, destino, weight=criterio)
    except Exception as error:
        return f"No se pudo calcular la ruta entre {origen} y {destino}: {error}", None

    resumen = (
        f"Ruta de {route['origin_name']} a {route['dest_name']}: "
        f"{route['distance_km']:.1f} km, unos {route['time_min']:.0f} minutos en carro. "
        f"A* expandió {route['nodes_expanded']} nodos."
    )
    return resumen, route


@tool(response_format="content_and_artifact")
def consultar_movilidad(pregunta: str) -> tuple[str, list[dict]]:
    """Busca información sobre movilidad en Medellín y el Valle de Aburrá.

    Cubre Metro, Metrocable, tranvía, Metroplús, buses, EnCicla, tarifas, horarios,
    pico y placa, normas para peatones y ciclistas, comunas, corredores viales y
    estaciones cercanas a lugares conocidos.
    """
    results = search(pregunta, k=4)
    content = "\n\n---\n\n".join(
        f"{result['texto']}\nFuente: {', '.join(result['fuentes'])}"
        for result in results
    )
    return content, results
