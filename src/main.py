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


DEFAULT_DAE_FILE = Path(__file__).parent / "Fichier_csv" / "geodae_larochelle.csv"


def get_place_geometry(place: str):
    """Retourne la géométrie OSM du lieu demandé."""

    # Recherche le lieu sur OpenStreetMap grâce à son nom.
    # Exemple : "La Rochelle, France"
    #
    # geocode_to_gdf() retourne les informations géographiques
    # du lieu sous forme de GeoDataFrame.
    #
    # .geometry récupère uniquement la géométrie.
    #
    # .union_all() permet d'obtenir une seule géométrie
    # représentant l'ensemble du lieu.

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


def create_map(
    place: str = "La Rochelle, France",
    dae_points: list[Point] | None = None,
    dae_file: Path = DEFAULT_DAE_FILE,
) -> folium.Map:
    """Construit la carte interactive avec des DAE regroupables par zoom."""

    # Récupère la forme géographique du lieu demandé.
    #
    # Ici par défaut :
    # "La Rochelle, France"
    geometry = get_place_geometry(place)

    # Si aucun point de DAE n'a été fourni manuellement, ils sont lus dans le
    # CSV puis filtrés avec la géométrie OSM du lieu demandé.
    if dae_points is None:
        dae_points = load_dae_points(dae_file, geometry)
    else:
        dae_points = [point for point in dae_points if geometry.covers(point)]

    # Trouve un point représentatif de la zone.
    # Il servira à déterminer le centre initial de la carte.
    center = geometry.representative_point()

    # Création de la carte interactive.
    map_view = folium.Map(
        # Centre de la carte
        location=[center.y, center.x],

        # Niveau de zoom initial
        zoom_start=13,

        # Affiche une échelle sur la carte
        control_scale=True,

        # Utilise OpenStreetMap comme fond de carte
        tiles="OpenStreetMap",
    )

    # Création d'un groupe permettant de regrouper
    # les marqueurs proches les uns des autres.
    #
    # Par exemple, au zoom arrière :
    #
    #       🔴 5
    #
    # puis en zoomant :
    #
    #       🔴   🔴
    #          🔴
    #       🔴   🔴
    marker_cluster = MarkerCluster(name="DAE").add_to(map_view)

    # Parcourt tous les points de DAE
    for dae_point in dae_points:

        # Création d'un marqueur sur la carte
        folium.Marker(

            # Folium veut [latitude, longitude]
            location=[dae_point.y, dae_point.x],

            # Texte affiché au survol
            tooltip="DAE",

            # Texte affiché lors du clic
            popup="Défibrillateur automatique externe",

            # Apparence du marqueur
            icon=folium.Icon(
                color="red",
                icon="plus-sign"
            ),

        # Ajoute le marqueur au groupe MarkerCluster
        ).add_to(marker_cluster)

    # Récupère les limites géographiques de la ville
    min_x, min_y, max_x, max_y = geometry.bounds

    # Ajuste automatiquement le zoom pour que
    # toute la zone de la ville soit visible.
    map_view.fit_bounds([
        [min_y, min_x],
        [max_y, max_x]
    ])

    # Retourne la carte créée
    return map_view


def main() -> None:

    # Création du parser permettant de récupérer
    # des arguments depuis la ligne de commande.
    parser = argparse.ArgumentParser(
        description="Génère la carte interactive des DAE."
    )

    # Argument permettant de choisir le nom du fichier HTML.
    #
    # Exemple :
    # python script.py --output carte.html
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("la_rochelle.html"),
        help="Fichier HTML de sortie.",
    )

    parser.add_argument(
        "--dae-file",
        type=Path,
        default=DEFAULT_DAE_FILE,
        help="CSV contenant les coordonnées des DAE.",
    )

    # Analyse les arguments fournis dans le terminal.
    args = parser.parse_args()

    # Création de la carte puis sauvegarde dans le fichier HTML.
    create_map(
        dae_file=args.dae_file,
    ).save(args.output)

    # Message affiché dans le terminal
    print(f"Carte interactive créée dans {args.output}")


# Cette condition signifie :
#
# "Si ce fichier est exécuté directement,
# alors lance la fonction main()."
if __name__ == "__main__":
    main()