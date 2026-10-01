"""Point d'entrée en ligne de commande."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import (
    DEFAULT_DAE_FILE,
    DEFAULT_OUTPUT_FILE,
    DEFAULT_PLACE,
    DEFAULT_POPULATION_FILE,
)
from .map_builder import create_map


def parse_args() -> argparse.Namespace:
    """Analyse les arguments de la ligne de commande."""

    parser = argparse.ArgumentParser(
        description="Génère la carte interactive des DAE."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Fichier HTML de sortie.",
    )
    parser.add_argument(
        "--place",
        default=DEFAULT_PLACE,
        help="Lieu OSM à cartographier.",
    )
    parser.add_argument(
        "--dae-file",
        type=Path,
        default=DEFAULT_DAE_FILE,
        help="CSV contenant les coordonnées des DAE.",
    )
    parser.add_argument(
        "--population-file",
        type=Path,
        default=DEFAULT_POPULATION_FILE,
        help="CSV contenant les carreaux et leur population.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    create_map(
        place=args.place,
        dae_file=args.dae_file,
        population_file=args.population_file,
    ).save(args.output)

    print(f"Carte interactive créée dans {args.output}")


if __name__ == "__main__":
    main()