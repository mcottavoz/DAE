import argparse
import csv
import re
from pathlib import Path

from pyproj import Transformer


SQUARE_SIZE = 200
ID_COLUMN = "idcar_200m"
OUTPUT_COORDINATE_COLUMNS = (
	"lon_bas_gauche",
	"lat_bas_gauche",
	"lon_haut_droit",
	"lat_haut_droit",
)

transformer = Transformer.from_crs(
	"EPSG:3035",
	"EPSG:4326",
	always_xy=True,
)

COORDINATE_PATTERN = re.compile(r"N(?P<y>\d+)E(?P<x>\d+)$")


def get_coordinates(square_id: str) -> tuple[float, float]:
	match = COORDINATE_PATTERN.search(square_id)
	if match is None:
		raise ValueError(f"Identifiant de carreau invalide : {square_id}")
	return float(match["x"]), float(match["y"])

def clean_csv(input_path: Path, output_path: Path) -> int:
	"""Ajoute les coordonnées géographiques aux carreaux de La Rochelle."""
	with input_path.open("r", encoding="utf-8-sig", newline="") as input_file:
		reader = csv.DictReader(input_file)
		if reader.fieldnames is None:
			raise ValueError("Le fichier CSV ne contient pas d'en-tête.")

		code_column = "lcog_geo"
		last_column = "ind"
		if code_column not in reader.fieldnames:
			raise ValueError(f"Colonne absente du CSV : {code_column}")
		if last_column not in reader.fieldnames:
			raise ValueError(f"Colonne absente du CSV : {last_column}")
		if ID_COLUMN not in reader.fieldnames:
			raise ValueError(f"Colonne absente du CSV : {ID_COLUMN}")

		columns = (
			reader.fieldnames[: reader.fieldnames.index(last_column) + 1]
			+ list(OUTPUT_COORDINATE_COLUMNS)
		)
		output_path.parent.mkdir(parents=True, exist_ok=True)
		rows_kept = 0
		with output_path.open("w", encoding="utf-8", newline="") as output_file:
			writer = csv.DictWriter(
				output_file,
				fieldnames=columns,
				extrasaction="ignore",
			)
			writer.writeheader()
			for row in reader:
				geo_codes = row[code_column].replace(",", " ").split()
				if "17300" in geo_codes:
					x, y = get_coordinates(row[ID_COLUMN])
					lon_bas_gauche, lat_bas_gauche = transformer.transform(x, y)
					lon_haut_droit, lat_haut_droit = transformer.transform(
						x + SQUARE_SIZE, y + SQUARE_SIZE
					)
					row.update(
						{
							"lon_bas_gauche": lon_bas_gauche,
							"lat_bas_gauche": lat_bas_gauche,
							"lon_haut_droit": lon_haut_droit,
							"lat_haut_droit": lat_haut_droit,
						}
					)
					writer.writerow(row)
					rows_kept += 1
	return rows_kept

def main() -> None:
	parser = argparse.ArgumentParser(
		description="Garde les carreaux de La Rochelle et les colonnes jusqu'à ind."
	)
	parser.add_argument(
		"input",
		nargs="?",
		type=Path,
		default=Path("src/Fichier_csv/carreaux_200m_la_rochelle.csv"),
		help="CSV source",
	)
	parser.add_argument(
		"output",
		nargs="?",
		type=Path,
		default=Path("src/Fichier_csv/carreaux_200m_la_rochelle_coord.csv"),
		help="CSV avec coordonnées géographiques à créer",
	)

	args = parser.parse_args()
	rows_kept = clean_csv(args.input, args.output)
	print(f"{rows_kept} ligne(s) conservée(s) dans {args.output}")


if __name__ == "__main__":
	main()