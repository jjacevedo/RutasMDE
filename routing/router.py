"""MOCK temporal de compute_route(). Se reemplaza por la versión real (A*) antes del miércoles.

Contrato (no cambiar sin avisar al grupo):
    compute_route(origin: str, destination: str, weight: str = "distance") -> dict
"""


def compute_route(origin: str, destination: str, weight: str = "distance") -> dict:
    return {
        "coords": [(6.2006, -75.5783), (6.2189, -75.5735), (6.2710, -75.5655)],
        "origin_coords": (6.2006, -75.5783),
        "dest_coords": (6.2710, -75.5655),
        "distance_km": 9.4,
        "time_min": 24.0,
        "nodes_expanded": 347,
        "origin_name": "Universidad EAFIT, El Poblado",
        "dest_name": "Parque Explora, Sevilla",
    }