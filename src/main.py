from __future__ import annotations

# Permet d'utiliser certaines annotations de types
# sans avoir besoin de résoudre immédiatement les types.

import argparse
import csv
from pathlib import Path

# Bibliothèque permettant de créer des cartes interactives
import folium

# Bibliothèque permettant de récupérer des données géographiques depuis OpenStreetMap.
import osmnx as ox

# Permet de regrouper plusieurs marqueurs sur la carte
from folium.plugins import MarkerCluster

# Représente un point géographique
from shapely.geometry import Point
from shapely.geometry import box


DEFAULT_DAE_FILE = Path(__file__).parent / "Fichier_csv" / "geodae_larochelle.csv"

DEFAULT_POPULATION_FILE = (
    Path(__file__).parent / "Fichier_csv" / "carreaux_200m_la_rochelle_coord.csv"
)


def get_place_geometry(place: str):
    """Retourne la géométrie OSM du lieu demandé."""

    return ox.geocode_to_gdf(place).geometry.union_all()


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


def load_population_cells(
    csv_path: Path,
    geometry
) -> list[dict[str, object]]:
    """Charge uniquement les carreaux présents dans le CSV."""

    source_cells = []

    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        for row in csv.DictReader(csv_file):
            try:
                lon_min = float(row["lon_bas_gauche"])
                lat_min = float(row["lat_bas_gauche"])
                lon_max = float(row["lon_haut_droit"])
                lat_max = float(row["lat_haut_droit"])
                population = float(row["ind"])
            except (KeyError, TypeError, ValueError):
                continue

            source_cells.append(
                {
                    "bounds": (
                        lon_min,
                        lat_min,
                        lon_max,
                        lat_max,
                    ),
                    "population": population,
                }
            )

    # Garde uniquement les carreaux réellement présents
    # dans le CSV et situés dans la zone géographique.
    return [
        cell
        for cell in source_cells
        if geometry.covers(box(*cell["bounds"]))
    ]


def population_color(
    population: float,
    thresholds: tuple[float, float, float]
) -> str:
    """Retourne une couleur selon quatre niveaux de population."""

    low, medium, high = thresholds

    if population <= low:
        return "#2ca25f"

    if population <= medium:
        return "#f1c40f"

    if population <= high:
        return "#f07818"

    return "#d73027"


def create_map(
    place: str = "La Rochelle, France",
    dae_points: list[Point] | None = None,
    dae_file: Path = DEFAULT_DAE_FILE,
    population_file: Path = DEFAULT_POPULATION_FILE,
) -> folium.Map:
    """Construit la carte interactive."""

    # Récupère la géométrie du lieu demandé.
    geometry = get_place_geometry(place)

    # Charge les DAE.
    if dae_points is None:
        dae_points = load_dae_points(
            dae_file,
            geometry
        )
    else:
        dae_points = [
            point
            for point in dae_points
            if geometry.covers(point)
        ]

    # Charge uniquement les carreaux présents dans le CSV.
    population_cells = load_population_cells(
        population_file,
        geometry
    )

    # Trouve un point représentatif de la zone.
    center = geometry.representative_point()

    # Création de la carte interactive.
    map_view = folium.Map(
        location=[
            center.y,
            center.x
        ],
        zoom_start=13,
        control_scale=True,
        tiles="OpenStreetMap",
    )

    # Affichage de la limite géographique OSM.
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

    # ------------------------------------------------------------------
    # COUCHE POPULATION
    # ------------------------------------------------------------------

    population_layer = folium.FeatureGroup(
        name="Population (carreaux de 200 m)",
        show=False,
    ).add_to(map_view)

    # Récupère les populations présentes dans le CSV.
    population_values = sorted(
        cell["population"]
        for cell in population_cells
    )

    # Détermine les trois seuils permettant de créer
    # quatre catégories de couleur.
    if population_values:
        population_thresholds = tuple(
            population_values[index]
            for index in (
                len(population_values) // 4,
                len(population_values) // 2,
                3 * len(population_values) // 4,
            )
        )
    else:
        population_thresholds = (0, 0, 0)

    # Dessine uniquement les carreaux réellement présents
    # dans le fichier CSV.
    for cell in population_cells:

        lon_min, lat_min, lon_max, lat_max = cell["bounds"]

        population = cell["population"]

        color = population_color(
            population,
            population_thresholds
        )

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
        ).add_to(population_layer)

    # ------------------------------------------------------------------
    # COUCHE DAE
    # ------------------------------------------------------------------

    # Groupe permettant de regrouper les marqueurs
    # lorsque la carte est dézoomée.
    marker_cluster = MarkerCluster(
        name="DAE"
    ).add_to(map_view)

    # Ajoute chaque DAE sur la carte.
    for dae_point in dae_points:

        folium.Marker(
            location=[
                dae_point.y,
                dae_point.x
            ],
            tooltip="DAE",
            popup="Défibrillateur automatique externe",
            icon=folium.Icon(
                color="red",
                icon="plus-sign"
            ),
        ).add_to(marker_cluster)

    # Contrôle permettant d'activer/désactiver
    # les différentes couches.
    folium.LayerControl(
        collapsed=False
    ).add_to(map_view)

    # ------------------------------------------------------------------
    # ZOOM AUTOMATIQUE
    # ------------------------------------------------------------------

    min_x, min_y, max_x, max_y = geometry.bounds

    map_view.fit_bounds(
        [
            [min_y, min_x],
            [max_y, max_x]
        ]
    )

    return map_view


def main() -> None:

    # Création du parser pour les arguments
    # de la ligne de commande.
    parser = argparse.ArgumentParser(
        description="Génère la carte interactive des DAE."
    )

    # Fichier HTML de sortie.
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("la_rochelle.html"),
        help="Fichier HTML de sortie.",
    )

    # Fichier CSV des DAE.
    parser.add_argument(
        "--dae-file",
        type=Path,
        default=DEFAULT_DAE_FILE,
        help="CSV contenant les coordonnées des DAE.",
    )

    # Fichier CSV de population.
    parser.add_argument(
        "--population-file",
        type=Path,
        default=DEFAULT_POPULATION_FILE,
        help="CSV contenant les carreaux et leur population.",
    )

    # Analyse des arguments.
    args = parser.parse_args()

    # Création puis sauvegarde de la carte.
    create_map(
        dae_file=args.dae_file,
        population_file=args.population_file,
    ).save(args.output)

    # Message affiché dans le terminal.
    print(
        f"Carte interactive créée dans {args.output}"
    )


# Si le fichier est exécuté directement,
# lance la fonction main().
if __name__ == "__main__":
    main()

