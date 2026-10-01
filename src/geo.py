"""Récupération des données géographiques depuis OpenStreetMap."""

import osmnx as ox


def get_place_geometry(place: str):
    """Retourne la géométrie OSM du lieu demandé."""

    return ox.geocode_to_gdf(place).geometry.union_all()