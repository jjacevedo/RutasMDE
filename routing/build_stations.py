"""Genera los JSON de estaciones para las capas del mapa.

Uso (desde la raíz del repo):
    python routing/build_stations.py

Fuente: OpenStreetMap (mismo origen que el grafo). Salida:
    routing/data/metro_stations.json    [{"name", "lat", "lon", "tipo"}]   tipo: metro | tranvia | cable
    routing/data/encicla_stations.json  [{"name", "lat", "lon"}]
"""

import json
from pathlib import Path

import osmnx as ox

DATA = Path(__file__).resolve().parent / "data"
PLACES = [
    "Medellín, Antioquia, Colombia",
    "Envigado, Antioquia, Colombia",
    "Itagüí, Antioquia, Colombia",
    "Bello, Antioquia, Colombia",
    "Sabaneta, Antioquia, Colombia",
    "La Estrella, Antioquia, Colombia",
]

TRANSIT_TAGS = {"railway": ["station", "halt", "tram_stop"], "aerialway": "station"}
ENCICLA_TAGS = {"amenity": "bicycle_rental"}

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


def _val(row, col):
    """Lee una columna que puede no existir o venir vacía (NaN)."""
    v = row.get(col)
    return None if v is None or v != v else v


def _tipo(row) -> str:
    if _val(row, "aerialway") == "station":
        return "cable"
    if _val(row, "railway") == "tram_stop" or _val(row, "station") == "tram" or _val(row, "tram") == "yes":
        return "tranvia"
    return "metro"


def gdf_to_records(gdf, with_tipo: bool, default_name: str | None = None) -> list[dict]:
    """GeoDataFrame de OSM -> lista de dicts. Un polígono (estación dibujada como
    área) se reduce a un punto interior; se eliminan duplicados por nombre."""
    records, seen = [], set()
    for _, row in gdf.iterrows():
        name = _val(row, "name") or default_name
        if not name or name in seen:
            continue
        seen.add(name)
        pt = row.geometry.representative_point()
        rec = {"name": name, "lat": round(pt.y, 6), "lon": round(pt.x, 6)}
        if with_tipo:
            rec["tipo"] = _tipo(row)
        records.append(rec)
    return sorted(records, key=lambda r: r["name"])


METRO_EXCLUDE = {
    "Antigua Estación de Bello del Ferrocarril",
    "El Morrón",
    "La Aldea",
    "Las Teresitas",
}
METRO_PREFIXES = ("Estación del Metro ", "Estación Metrocable ", "Estación ")
TIPO_OVERRIDE = {"San Antonio": "metro", "San Javier": "metro"}


def clean_metro(records: list[dict]) -> list[dict]:
    """Quita lo que no es del Metro, limpia prefijos del nombre y elimina duplicados."""
    out, seen = [], set()
    for r in records:
        if r["name"] in METRO_EXCLUDE:
            continue
        name = r["name"]
        for prefix in METRO_PREFIXES:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break
        if name in seen:
            continue
        seen.add(name)
        out.append({**r, "name": name, "tipo": TIPO_OVERRIDE.get(name, r["tipo"])})
    return sorted(out, key=lambda r: r["name"])


def clean_encicla(records: list[dict]) -> list[dict]:
    """Pone un nombre legible a las estaciones que no tienen nombre en OSM."""
    out, n = [], 0
    for r in sorted(records, key=lambda r: (r["lat"], r["lon"])):
        if r["name"].startswith("EnCicla ") and r["name"][8:].isdigit():
            n += 1
            r = {**r, "name": f"Estación EnCicla sin nombre {n}"}
        out.append(r)
    return sorted(out, key=lambda r: r["name"])


def _save(records: list[dict], filename: str) -> None:
    path = DATA / filename
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  {len(records):4d} estaciones -> {path}")


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    print("Descargando estaciones de Metro, tranvía y cables...")
    transit = with_overpass_fallback(ox.features_from_place, PLACES, tags=TRANSIT_TAGS)
    _save(clean_metro(gdf_to_records(transit, with_tipo=True)), "metro_stations.json")

    print("Descargando estaciones de EnCicla...")
    encicla = with_overpass_fallback(ox.features_from_place, PLACES, tags=ENCICLA_TAGS)
    encicla = encicla.reset_index()
    encicla["name"] = encicla.apply(lambda r: _val(r, "name") or f"EnCicla {r['id']}", axis=1)
    _save(clean_encicla(gdf_to_records(encicla, with_tipo=False)), "encicla_stations.json")


if __name__ == "__main__":
    main()