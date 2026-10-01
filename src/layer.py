"""Construction des différentes couches de la carte folium."""

from __future__ import annotations

import folium
from folium.plugins import MarkerCluster
from shapely.geometry import Point

from .population import compute_thresholds, population_color


def add_boundary_layer(map_view: folium.Map, geometry, place: str) -> None:
    """Ajoute la limite géographique OSM (masquée par défaut)."""

    folium.GeoJson(
        data=geometry.__geo_interface__,
        name="Limite géométrique OSM",
        show=False,
        style_function=lambda _feature: {
            "color": "#1769aa",
            "weight": 3,
            "fill": False,
        },
        tooltip=f"Zone OSM : {place}",
    ).add_to(map_view)


def add_population_layer(
    map_view: folium.Map,
    population_cells: list[dict[str, object]],
) -> None:
    """Ajoute les carreaux de population colorés par niveau."""

    layer = folium.FeatureGroup(
        name="Population (carreaux de 200 m)",
        show=False,
    ).add_to(map_view)

    thresholds = compute_thresholds(population_cells)

    for cell in population_cells:
        lon_min, lat_min, lon_max, lat_max = cell["bounds"]
        population = cell["population"]
        color = population_color(population, thresholds)

        folium.Polygon(
            locations=[
                [lat_min, lon_min],
                [lat_min, lon_max],
                [lat_max, lon_max],
                [lat_max, lon_min],
            ],
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.35,
            weight=1,
            tooltip=f"Population estimée : {population:g}",
        ).add_to(layer)


def add_dae_layer(map_view: folium.Map, dae_points: list[Point]) -> None:
    """Ajoute les DAE, regroupés en clusters quand on dézoome."""

    cluster = MarkerCluster(name="DAE").add_to(map_view)

    for point in dae_points:
        folium.Marker(
            location=[point.y, point.x],
            tooltip="DAE",
            popup="Défibrillateur automatique externe",
            icon=folium.Icon(color="red", icon="plus-sign"),
        ).add_to(cluster)