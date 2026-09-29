"""Keep the cleaned DAE located in La Rochelle (with a margin around the city).

    python select_zone.py
    python select_zone.py Fichier_csv/geodae_clean.csv Fichier_csv/geodae_larochelle.csv

The margin keeps the DAE just outside the city: they can still cover the
population tiles on its border.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1] / "Fichier_csv"
DEFAULT_INPUT = DATA_DIR / "geodae_clean.csv"
DEFAULT_OUTPUT = DATA_DIR / "geodae_larochelle.csv"

# Approximate bounding box of the commune of La Rochelle (lat / lon, WGS84).
LAT_MIN, LAT_MAX = 46.135, 46.190
LON_MIN, LON_MAX = -1.240, -1.100

# Margin around the box: 0.006° is about 650 m in latitude and 460 m in longitude.
MARGIN_DEG = 0.006


def select_la_rochelle(input_path: Path, output_path: Path, margin: float = MARGIN_DEG) -> int:
	dae = pd.read_csv(input_path, dtype=str, keep_default_na=False)
	lat = pd.to_numeric(dae["c_lat_coor1"], errors="coerce")
	lon = pd.to_numeric(dae["c_long_coor1"], errors="coerce")

	inside = (
		lat.between(LAT_MIN - margin, LAT_MAX + margin)
		& lon.between(LON_MIN - margin, LON_MAX + margin)
	)
	selected = dae[inside]

	output_path.parent.mkdir(parents=True, exist_ok=True)
	selected.to_csv(output_path, index=False, encoding="utf-8")
	return len(selected)


def main() -> None:
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
	parser.add_argument("output", nargs="?", type=Path, default=DEFAULT_OUTPUT)
	parser.add_argument("--margin", type=float, default=MARGIN_DEG, help="marge en degrés (défaut : %(default)s)")
	args = parser.parse_args()

	count = select_la_rochelle(args.input, args.output, args.margin)
	print(f"{count} DAE à La Rochelle écrits dans {args.output}")


if __name__ == "__main__":
	main()
