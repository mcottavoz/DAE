from __future__ import annotations

# Permet d'utiliser certaines annotations de types
# sans avoir besoin de résoudre immédiatement les types.


import argparse
import random
from pathlib import Path

# Bibliothèque permettant de créer des cartes interactives
import folium

# Bibliothèque permettant de récupérer des données géographiques depuis OpenStreetMap.
import osmnx as ox

# Permet de regrouper plusieurs marqueurs sur la carte
from folium.plugins import MarkerCluster

# Représente un point géographique
from shapely.geometry import Point


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


def random_point_in_geometry(
    geometry,
    generator: random.Random
) -> Point:
    """Génère un point aléatoire contenu dans une géométrie."""

    # Récupère les limites de la zone :
    #
    # min_x = longitude minimale
    # min_y = latitude minimale
    # max_x = longitude maximale
    # max_y = latitude maximale
    min_x, min_y, max_x, max_y = geometry.bounds

    # On essaye au maximum 1000 fois
    # de trouver un point situé à l'intérieur de la zone.
    for _ in range(1_000):

        # Génère une longitude et une latitude aléatoires
        # à l'intérieur du rectangle contenant la zone.
        point = Point(
            generator.uniform(min_x, max_x),
            generator.uniform(min_y, max_y),
        )

        # Vérifie si le point est réellement à l'intérieur
        # de la géométrie.
        if geometry.contains(point):
            return point

    # Si aucun point n'a été trouvé après 1000 essais,
    # on retourne un point représentatif de la géométrie.
    return geometry.representative_point()


def create_map(
    place: str = "La Rochelle, France",
    seed: int | None = None,
    dae_points: list[Point] | None = None,
    dae_count: int = 5,
) -> folium.Map:
    """Construit la carte interactive avec des DAE regroupables par zoom."""

    # Récupère la forme géographique du lieu demandé.
    #
    # Ici par défaut :
    # "La Rochelle, France"
    geometry = get_place_geometry(place)

    # Si aucun point de DAE n'a été fourni manuellement...
    if dae_points is None:

        # Création d'un générateur aléatoire.
        #
        # seed permet de reproduire exactement
        # les mêmes points aléatoires.
        generator = random.Random(seed)

        # Création de dae_count points aléatoires
        # à l'intérieur de la ville.
        dae_points = [
            random_point_in_geometry(geometry, generator)
            for _ in range(dae_count)
        ]

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

    # Argument permettant de choisir la seed.
    #
    # Exemple :
    # python script.py --seed 42
    parser.add_argument(
        "--seed",
        type=int,
        help="Graine optionnelle pour reproduire le point."
    )

    # Argument permettant de choisir le nombre de DAE.
    #
    # Exemple :
    # python script.py --count 20
    #
    # choices=range(1, 101)
    # signifie qu'on accepte uniquement les valeurs
    # comprises entre 1 et 100.
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        choices=range(1, 101),
        help="Nombre de DAE de démonstration (entre 1 et 100).",
    )

    # Analyse les arguments fournis dans le terminal.
    args = parser.parse_args()

    # Création de la carte puis sauvegarde dans le fichier HTML.
    create_map(
        seed=args.seed,
        dae_count=args.count
    ).save(args.output)

    # Message affiché dans le terminal
    print(f"Carte interactive créée dans {args.output}")


# Cette condition signifie :
#
# "Si ce fichier est exécuté directement,
# alors lance la fonction main()."
if __name__ == "__main__":
    main()