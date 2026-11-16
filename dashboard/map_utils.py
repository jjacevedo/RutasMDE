"""Folium map construction and transit-station data loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import folium
from folium.plugins import Fullscreen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CENTER = (6.2442, -75.5812)
METRO_PATH = ROOT / "routing" / "data" / "metro_stations.json"
ENCICLA_PATH = ROOT / "routing" / "data" / "encicla_stations.json"


def _load_stations(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open(encoding="utf-8") as source:
            values = json.load(source)
    except (OSError, json.JSONDecodeError):
        return []
    return [
        item for item in values
        if isinstance(item, dict)
        and isinstance(item.get("lat"), (int, float))
        and isinstance(item.get("lon"), (int, float))
    ] if isinstance(values, list) else []


def load_metro_stations() -> list[dict[str, Any]]:
    return _load_stations(METRO_PATH)


def load_encicla_stations() -> list[dict[str, Any]]:
    return _load_stations(ENCICLA_PATH)


def _popup_html(data: dict[str, Any], label: str) -> str:
    name = str(data.get("name", label)).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    details = "".join(
        f"<br><small>{str(key).replace('_', ' ').title()}: {str(value)}</small>"
        for key, value in data.items() if key not in {"name", "lat", "lon"} and value not in (None, "")
    )
    return f"<b>{name}</b>{details}"


def _coordinate(value: Any) -> tuple[float, float] | None:
    """Normalize an (lat, lon) pair and reject likely (lon, lat) swaps."""
    try:
        lat, lon = float(value[0]), float(value[1])
    except (TypeError, ValueError, IndexError, KeyError):
        return None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    # This dashboard is for Medellin. A swapped coordinate will typically put
    # longitude in the latitude slot and be rejected by the latitude bound.
    return (lat, lon)


def build_route_map(
    route: dict[str, Any] | None = None,
    *,
    show_metro: bool = True,
    show_encicla: bool = True,
    metro_stations: list[dict[str, Any]] | None = None,
    encicla_stations: list[dict[str, Any]] | None = None,
) -> folium.Map:
    """Create the map; route coordinates follow Rol B's (latitude, longitude) contract."""
    coords: list[tuple[float, float]] = []
    if isinstance(route, dict):
        raw_coords = route.get("coords") or []
        if isinstance(raw_coords, (list, tuple)):
            coords = [point for item in raw_coords if (point := _coordinate(item)) is not None]

    origin = _coordinate(route.get("origin_coords")) if isinstance(route, dict) else None
    destination = _coordinate(route.get("dest_coords")) if isinstance(route, dict) else None
    points = [point for point in (origin, destination) if point is not None] or coords
    center = (
        (sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points))
        if points else DEFAULT_CENTER
    )
    map_obj = folium.Map(location=center, zoom_start=13, control_scale=True, tiles="OpenStreetMap")
    Fullscreen(position="topright").add_to(map_obj)

    if coords:
        folium.PolyLine(coords, color="#2563eb", weight=6, opacity=0.88, tooltip="Ruta calculada por A*").add_to(map_obj)
    if origin:
        folium.Marker(origin, tooltip="Origen", popup=_popup_html({"name": route.get("origin_name", "Origen")}, "Origen"),
                      icon=folium.Icon(color="green", icon="play")).add_to(map_obj)
    if destination:
        folium.Marker(destination, tooltip="Destino", popup=_popup_html({"name": route.get("dest_name", "Destino")}, "Destino"),
                      icon=folium.Icon(color="red", icon="flag")).add_to(map_obj)

    if show_metro:
        layer = folium.FeatureGroup(name="Metro, tranvía y cables", show=True)
        for station in metro_stations if metro_stations is not None else load_metro_stations():
            folium.CircleMarker(
                location=(station["lat"], station["lon"]), radius=5, color="#7c3aed",
                fill=True, fill_opacity=0.9, tooltip=station.get("name", "Estación"),
                popup=_popup_html(station, "Estación"),
            ).add_to(layer)
        layer.add_to(map_obj)
    if show_encicla:
        layer = folium.FeatureGroup(name="EnCicla", show=True)
        for station in encicla_stations if encicla_stations is not None else load_encicla_stations():
            folium.CircleMarker(
                location=(station["lat"], station["lon"]), radius=4, color="#0891b2",
                fill=True, fill_opacity=0.85, tooltip=station.get("name", "Estación EnCicla"),
                popup=_popup_html(station, "Estación EnCicla"),
            ).add_to(layer)
        layer.add_to(map_obj)

    if coords:
        map_obj.fit_bounds(coords, padding=(24, 24))
    elif origin and destination:
        map_obj.fit_bounds([origin, destination], padding=(24, 24))
    folium.LayerControl(collapsed=False).add_to(map_obj)
    return map_obj

