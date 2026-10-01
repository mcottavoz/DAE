"""Lecture des fichiers CSV (DAE et population)."""

from __future__ import annotations

import csv
from pathlib import Path

from shapely.geometry import Point, box


def load_dae_points(csv_path: Path, geometry) -> list[Point]:
    """Charge les DAE du CSV et conserve ceux couverts par la zone OSM."""

    dae_points = []

    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        for row in csv.DictReader(csv_file):
            try:
                point = Point(
                    float(row["c_long_coor1"]),
                    float(row["c_lat_coor1"]),
                )
            except (KeyError, TypeError, ValueError):
                continue

            if geometry.covers(point):
                dae_points.append(point)

    return dae_points


def load_population_cells(csv_path: Path, geometry) -> list[dict[str, object]]:
    """Charge les carreaux du CSV situés dans la zone géographique."""

    source_cells = []

    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        for row in csv.DictReader(csv_file):
            try:
                bounds = (
                    float(row["lon_bas_gauche"]),
                    float(row["lat_bas_gauche"]),
                    float(row["lon_haut_droit"]),
                    float(row["lat_haut_droit"]),
                )
                population = float(row["ind"])
            except (KeyError, TypeError, ValueError):
                continue

            source_cells.append({"bounds": bounds, "population": population})

    return [
        cell
        for cell in source_cells
        if geometry.covers(box(*cell["bounds"]))
    ]