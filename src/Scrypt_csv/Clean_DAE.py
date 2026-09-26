"""Filter the DAE CSV to validated and accessible defibrillators."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable


DEFAULT_INPUT = Path(__file__).resolve().parents[1] / "Fichier_csv" / "geodae_cut.csv"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "Fichier_csv" / "geodae_filtered.csv"
CSV_ENCODING = "utf-8"


def _normalise(value: str | None) -> str:
	"""Normalise a CSV value for comparisons without changing output data."""
	normalised = (value or "").replace("‚", "é")
	return " ".join(normalised.strip().casefold().split())


def _is_eligible(row: dict[str, str]) -> bool:
	"""Return whether a row is validated and accessible at all times or outdoors."""
	is_validated = _normalise(row.get("c_etat_valid")) == "validées"
	is_outdoor = _normalise(row.get("c_acc")) == "extérieur"
	display_hours = _normalise(row.get("c_disp_h"))
	is_open_all_day = "24h/24" in display_hours
	is_business_hours_only = "heures ouvrables" in display_hours
	return is_validated and not is_business_hours_only and (is_outdoor or is_open_all_day)


def _deduplicate(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
	"""Remove duplicate records while ignoring the unique ``gid`` column."""
	unique_rows: list[dict[str, str]] = []
	seen: set[tuple[tuple[str, str], ...]] = set()

	for row in rows:
		key = tuple(
			sorted(
				(column, _normalise(value))
				for column, value in row.items()
				if column != "gid"
			)
		)
		if key not in seen:
			seen.add(key)
			unique_rows.append(row)

	return unique_rows


def filter_dae_csv(input_path: Path, output_path: Path) -> int:
	"""Write the filtered CSV and return the number of rows written."""
	with input_path.open(
		"r", encoding=CSV_ENCODING, errors="replace", newline=""
	) as input_file:
		reader = csv.DictReader(input_file)
		if reader.fieldnames is None:
			raise ValueError("Le fichier CSV ne contient pas d'en-tête.")

		filtered_rows = _deduplicate(
			row for row in reader if _is_eligible(row)
		)

	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open(
		"w", encoding=CSV_ENCODING, errors="replace", newline=""
	) as output_file:
		writer = csv.DictWriter(output_file, fieldnames=reader.fieldnames)
		writer.writeheader()
		writer.writerows(filtered_rows)

	return len(filtered_rows)


def main() -> None:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
	parser.add_argument("output", nargs="?", type=Path, default=DEFAULT_OUTPUT)
	args = parser.parse_args()

	count = filter_dae_csv(args.input, args.output)
	print(f"{count} ligne(s) écrite(s) dans {args.output}")


if __name__ == "__main__":
	main()
