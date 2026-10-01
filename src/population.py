"""Logique métier liée à la population : seuils et couleurs."""

from __future__ import annotations

from .config import POPULATION_COLORS

Thresholds = tuple[float, float, float]


def compute_thresholds(population_cells: list[dict[str, object]]) -> Thresholds:
    """Calcule les trois quartiles qui délimitent les quatre niveaux."""

    values = sorted(cell["population"] for cell in population_cells)

    if not values:
        return (0, 0, 0)

    n = len(values)
    return (values[n // 4], values[n // 2], values[3 * n // 4])


def population_color(population: float, thresholds: Thresholds) -> str:
    """Retourne une couleur selon quatre niveaux de population."""

    low, medium, high = thresholds
    c_low, c_medium, c_high, c_top = POPULATION_COLORS

    if population <= low:
        return c_low
    if population <= medium:
        return c_medium
    if population <= high:
        return c_high
    return c_top