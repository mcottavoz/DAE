"""Keep DAE records located in the central La Rochelle area."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable


DEFAULT_INPUT = Path(__file__).resolve().parents[1] / "Fichier_csv" / "geodae_filtered.csv"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "Fichier_csv" / "geodae_zone.csv"
CSV_ENCODING = "utf-8"

# Approximate bounding box for central La Rochelle.
MIN_LATITUDE = 46.14
MAX_LATITUDE = 46.18
MIN_LONGITUDE = -1.18
MAX_LONGITUDE = -1.10


def _normalise(value: str | None) -> str:
	"""Normalise a CSV value for comparisons without changing output data."""
	normalised = (value or "").replace("‚", "é")
	return " ".join(normalised.strip().casefold().split())


def _is_in_zone(
	row: dict[str, str],
	min_latitude: float,
	max_latitude: float,
	min_longitude: float,
	max_longitude: float,
) -> bool:
	"""Return whether a row's coordinates are inside the selected bounding box."""
	try:
		latitude = float(row["c_lat_coor1"])
		longitude = float(row["c_long_coor1"])
	except (KeyError, TypeError, ValueError):
		return False

	return (
		min_latitude <= latitude <= max_latitude
		and min_longitude <= longitude <= max_longitude
	)


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


def filter_dae_csv(
	input_path: Path,
	output_path: Path,
	min_latitude: float = MIN_LATITUDE,
	max_latitude: float = MAX_LATITUDE,
	min_longitude: float = MIN_LONGITUDE,
	max_longitude: float = MAX_LONGITUDE,
) -> int:
	"""Write the filtered CSV and return the number of rows written."""
	if min_latitude > max_latitude or min_longitude > max_longitude:
		raise ValueError("Les limites géographiques sont invalides.")

	with input_path.open(
		"r", encoding=CSV_ENCODING, errors="replace", newline=""
	) as input_file:
		reader = csv.DictReader(input_file)
		if reader.fieldnames is None:
			raise ValueError("Le fichier CSV ne contient pas d'en-tête.")

		filtered_rows = _deduplicate(
			row
			for row in reader
			if _is_in_zone(
				row,
				min_latitude,
				max_latitude,
				min_longitude,
				max_longitude,
			)
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
	parser.add_argument("--min-latitude", type=float, default=MIN_LATITUDE)
	parser.add_argument("--max-latitude", type=float, default=MAX_LATITUDE)
	parser.add_argument("--min-longitude", type=float, default=MIN_LONGITUDE)
	parser.add_argument("--max-longitude", type=float, default=MAX_LONGITUDE)
	args = parser.parse_args()

	count = filter_dae_csv(
		args.input,
		args.output,
		args.min_latitude,
		args.max_latitude,
		args.min_longitude,
		args.max_longitude,
	)
	print(f"{count} ligne(s) écrite(s) dans {args.output}")


if __name__ == "__main__":
	main()
