"""Assemblage de la carte à partir des données et des couches."""

from __future__ import annotations

from pathlib import Path

import folium
from shapely.geometry import Point

from .config import (
    DEFAULT_DAE_FILE,
    DEFAULT_PLACE,
    DEFAULT_POPULATION_FILE,
    DEFAULT_ZOOM,
)
from .data_loader import load_dae_points, load_population_cells
from .geo import get_place_geometry
from .layer import add_boundary_layer, add_dae_layer, add_population_layer


def create_map(
    place: str = DEFAULT_PLACE,
    dae_points: list[Point] | None = None,
    dae_file: Path = DEFAULT_DAE_FILE,
    population_file: Path = DEFAULT_POPULATION_FILE,
) -> folium.Map:
    """Construit la carte interactive."""

    geometry = get_place_geometry(place)

    # Chargement des données
    if dae_points is None:
        dae_points = load_dae_points(dae_file, geometry)
    else:
        dae_points = [p for p in dae_points if geometry.covers(p)]

    population_cells = load_population_cells(population_file, geometry)

    # Création de la carte
    center = geometry.representative_point()
    map_view = folium.Map(
        location=[center.y, center.x],
        zoom_start=DEFAULT_ZOOM,
        control_scale=True,
        tiles="OpenStreetMap",
    )

    # Couches
    add_boundary_layer(map_view, geometry, place)
    add_population_layer(map_view, population_cells)
    add_dae_layer(map_view, dae_points)

    folium.LayerControl(collapsed=False).add_to(map_view)

    # Zoom automatique sur la zone
    min_x, min_y, max_x, max_y = geometry.bounds
    map_view.fit_bounds([[min_y, min_x], [max_y, max_x]])

    return map_view