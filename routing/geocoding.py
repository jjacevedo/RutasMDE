"""Geocodificación: texto -> coordenadas (geopy/Nominatim) y coordenadas -> nodo del grafo.

Nominatim permite ~1 petición por segundo, así que:
  - se usa RateLimiter (espera 1 s entre peticiones)
  - cada resultado se guarda en routing/data/geocode_cache.json (este archivo SÍ se sube a git:
    así la demo funciona aunque Nominatim falle). Si Nominatim ubica mal un lugar, se corrige
    a mano en ese JSON.

Precargar la caché con los lugares de la evaluación:
    python -m routing.geocoding
"""

import json
import unicodedata
from pathlib import Path

import osmnx as ox
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim

CACHE_PATH = Path(__file__).resolve().parent / "data" / "geocode_cache.json"

VIEWBOX = [(6.10, -75.72), (6.40, -75.45)]

MAX_SNAP_M = 1500

_geolocator = Nominatim(user_agent="rutasmde-eafit-si3003", timeout=10)
_geocode_limited = RateLimiter(_geolocator.geocode, min_delay_seconds=1.1, max_retries=2)
_cache: dict | None = None


def _normalize(text: str) -> str:
    """'  Universidad EAFIT ' -> 'universidad eafit'; quita tildes para que
    'Itagüí' e 'itagui' sean la misma llave de caché."""
    text = unicodedata.normalize("NFKD", text.strip().lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return " ".join(text.split())


def _load_cache() -> dict:
    global _cache
    if _cache is None:
        _cache = json.loads(CACHE_PATH.read_text(encoding="utf-8")) if CACHE_PATH.exists() else {}
    return _cache


def _save_cache() -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(_load_cache(), ensure_ascii=False, indent=2, sort_keys=True),
                          encoding="utf-8")


def geocode_with_name(place: str) -> tuple[float, float, str]:
    """Devuelve (lat, lon, nombre_corto). Lanza ValueError si no lo encuentra."""
    key = _normalize(place)
    if not key:
        raise ValueError("El lugar está vacío")

    cache = _load_cache()
    if key in cache:
        hit = cache[key]
        return hit["lat"], hit["lon"], hit["name"]

    query = place if "colombia" in key else f"{place}, Antioquia, Colombia"
    location = _geocode_limited(query, viewbox=VIEWBOX, bounded=True, country_codes="co")
    if location is None:
        raise ValueError(f"No encontré '{place}' en el área metropolitana de Medellín")

    name = ", ".join(part.strip() for part in location.address.split(",")[:2])
    cache[key] = {"lat": location.latitude, "lon": location.longitude, "name": name}
    _save_cache()
    return location.latitude, location.longitude, name


def geocode(place: str) -> tuple[float, float]:
    """Contrato del plan: lugar -> (lat, lon)."""
    lat, lon, _ = geocode_with_name(place)
    return lat, lon


def nearest_node(G, lat: float, lon: float) -> int:
    """Nodo del grafo más cercano a (lat, lon). OJO: X = longitud, Y = latitud."""
    node, dist_m = ox.distance.nearest_nodes(G, X=lon, Y=lat, return_dist=True)
    if dist_m > MAX_SNAP_M:
        raise ValueError(f"El punto ({lat:.4f}, {lon:.4f}) está a {dist_m:.0f} m de la vía más "
                         "cercana del grafo: probablemente está fuera del área cubierta")
    return int(node)


EVAL_PLACES = [
    "Universidad EAFIT", "Parque Berrío", "Laureles", "El Poblado", "Estación Industriales",
    "Parque Explora", "Itagüí", "Avenida El Poblado", "Centro, Medellín", "Buenos Aires, Medellín",
    "Aeropuerto Olaya Herrera", "Centro Comercial Santafé, Medellín", "Comuna 13, Medellín",
    "Envigado", "Universidad Nacional, Medellín", "Belén, Medellín", "Castilla, Medellín",
    "Estadio Atanasio Girardot", "Estación San Antonio", "Universidad de Antioquia",
]

if __name__ == "__main__":
    print(f"Precargando {len(EVAL_PLACES)} lugares (1 por segundo)...\n")
    for p in EVAL_PLACES:
        try:
            lat, lon, name = geocode_with_name(p)
            print(f"  OK   {p:38s} -> ({lat:.5f}, {lon:.5f})  {name}")
        except Exception as e:
            print(f"  FALLA {p:37s} -> {e}")
    print(f"\nCaché guardada en {CACHE_PATH}. Revisa en Google Maps las coordenadas dudosas.")