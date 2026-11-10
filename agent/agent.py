"""Mock temporal de run_agent(). Se reemplaza por el agente real en la integración."""

MOCK_ROUTE = {
    "coords": [
        (6.2006, -75.5783),
        (6.2081, -75.5768),
        (6.2189, -75.5735),
        (6.2350, -75.5702),
        (6.2512, -75.5680),
        (6.2635, -75.5662),
        (6.2710, -75.5655),
    ],
    "origin_coords": (6.2006, -75.5783),
    "dest_coords": (6.2710, -75.5655),
    "distance_km": 9.4,
    "time_min": 24.0,
    "nodes_expanded": 347,
    "origin_name": "Universidad EAFIT, El Poblado",
    "dest_name": "Parque Explora, Sevilla",
}

ROUTE_KEYWORDS = ("ruta", "llego", "llegar", "ir de", "como voy", "cómo voy")


def run_agent(user_message: str, chat_history: list) -> dict:
    text = user_message.lower()

    if any(keyword in text for keyword in ROUTE_KEYWORDS):
        return {
            "response": (
                "Para ir de la Universidad EAFIT al Parque Explora hay unos 9.4 km "
                "en carro, aproximadamente 24 minutos. En transporte público puedes "
                "tomar el Metro en la estación Aguacatala hacia el norte y bajarte "
                "en la estación Universidad."
            ),
            "route": MOCK_ROUTE,
            "sources": [
                "La Línea A del Metro de Medellín conecta La Estrella con Niquía.",
                "La estación Universidad queda junto al Parque Explora y el Jardín Botánico.",
            ],
        }

    return {
        "response": (
            "Soy RutasMDE, tu copiloto de movilidad en Medellín. Puedo calcular "
            "rutas entre dos lugares y responder preguntas sobre el Metro, "
            "EnCicla y el transporte público de la ciudad."
        ),
        "route": None,
        "sources": [],
    }
