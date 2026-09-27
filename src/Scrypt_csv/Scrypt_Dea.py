"""Nettoie le fichier des carreaux 200 m pour ne garder que La Rochelle."""

import argparse
import csv
from pathlib import Path


def clean_csv(input_path: Path, output_path: Path) -> int:
	"""Garde les colonnes jusqu'à ind et les lignes contenant le code 17300."""
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

		columns = reader.fieldnames[: reader.fieldnames.index(last_column) + 1]
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
		default=Path("src/Fichier_csv/carreaux_200m_met.csv"),
		help="CSV source",
	)
	parser.add_argument(
		"output",
		nargs="?",
		type=Path,
		default=Path("src/Fichier_csv/carreaux_200m_la_rochelle.csv"),
		help="CSV nettoyé à créer",
	)
	args = parser.parse_args()

	rows_kept = clean_csv(args.input, args.output)
	print(f"{rows_kept} ligne(s) conservée(s) dans {args.output}")


if __name__ == "__main__":
	main()
