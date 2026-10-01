"""Clean the raw Géo'DAE export (geodae.csv from data.gouv.fr).

Removes every record that cannot be treated as a real, fixed, working
defibrillator at a trustworthy location. No zone or availability filter here.

Cleaning steps, in order (each one is counted and reported):
    1. not validated          c_etat_valid != "validées"
    2. not active             c_etat != "Actif"
    3. not working            c_etat_fonct != "En fonctionnement"
    4. mobile device          c_dae_mobile == "t" (no fixed position)
    5. invalid coordinates    missing, out of range, or (0, 0)
    6. flagged duplicate      c_doublon == "t" (flag set by the database)
    7. spatial duplicate      closer than --dup-radius metres AND same name or
                              same operator (SIREN); the most recently updated
                              record of each group is kept
    8. stacked geolocation    at least --min-stack records at the same point
                              (~1 m) with different addresses: devices geocoded
                              to the town hall

Output columns: the original fields gid, c_etat_valid, c_nom, c_lat_coor1,
c_long_coor1 (as clean decimal numbers), c_acc, c_acc_lib, c_disp_j, c_disp_h,
c_etat_fonct, c_doublon, plus is_24_7 (available 7 days a week, 24 hours a day).
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree


DATA_DIR = Path(__file__).resolve().parents[1] / "Fichier_csv"
DEFAULT_INPUT = DATA_DIR / "geodae.csv"
DEFAULT_OUTPUT = DATA_DIR / "geodae_clean.csv"

EARTH_RADIUS_M = 6_371_000.0
DEFAULT_DUP_RADIUS_M = 10.0
DEFAULT_MIN_STACK = 3
STACK_ROUNDING = 5  # 5 decimals of a degree is about 1 m
WEEK_DAYS = {"lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"}

# Columns read from the raw file: only those used by a cleaning step or kept.
INPUT_COLUMNS = [
	"gid", "c_nom", "c_lat_coor1", "c_long_coor1",      # identity and position
	"c_etat_valid", "c_etat", "c_etat_fonct",            # steps 1-3
	"c_dae_mobile", "c_doublon",                         # steps 4 and 6
	"c_expt_siren", "c_maj_don",                         # step 7
	"c_adr_num", "c_adr_voie", "c_com_insee",            # step 8
	"c_acc", "c_acc_lib", "c_disp_j", "c_disp_h",        # scenarios
]
OUTPUT_COLUMNS = [
	"gid", "c_etat_valid", "c_nom", "c_lat_coor1", "c_long_coor1",
	"c_acc", "c_acc_lib", "c_disp_j", "c_disp_h", "c_etat_fonct",
	"c_doublon", "is_24_7",
]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def normalise(series: pd.Series) -> pd.Series:
	"""Lower-case, trim and collapse spaces, for comparisons only."""
	return (
		series.fillna("").astype(str)
		.str.normalize("NFC").str.casefold()
		.str.replace(r"\s+", " ", regex=True).str.strip()
	)


def parse_pg_array(value: str) -> list[str]:
	"""Parse a PostgreSQL array literal such as ``{lundi,"heures ouvrables"}``."""
	value = (value or "").strip()
	if value.startswith("{") and value.endswith("}"):
		value = value[1:-1]
	if not value:
		return []
	items = next(csv.reader([value], quotechar='"', skipinitialspace=True))
	return [" ".join(item.strip().casefold().split()) for item in items if item.strip()]


def to_ecef(lat_deg: np.ndarray, lon_deg: np.ndarray) -> np.ndarray:
	"""Lat/lon to 3D metres on a sphere: exact enough for points a few metres apart."""
	lat, lon = np.radians(lat_deg), np.radians(lon_deg)
	return EARTH_RADIUS_M * np.column_stack(
		(np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat))
	)


def read_raw(path: Path) -> pd.DataFrame:
	"""Read the raw export (``;`` separated). Try UTF-8 first, then cp1252."""
	for encoding in ("utf-8-sig", "cp1252"):
		try:
			df = pd.read_csv(
				path, sep=";", dtype=str, keep_default_na=False, encoding=encoding,
				usecols=lambda column: column in INPUT_COLUMNS,
			)
		except UnicodeDecodeError:
			continue
		if encoding != "utf-8-sig":
			print(f"Attention : fichier lu en {encoding}, vérifiez les accents.", file=sys.stderr)
		missing = [column for column in INPUT_COLUMNS if column not in df.columns]
		if missing:
			print(f"Attention : colonnes absentes : {', '.join(missing)}", file=sys.stderr)
			df = df.assign(**{column: "" for column in missing})
		return df
	raise ValueError(f"Impossible de décoder {path}.")


# --------------------------------------------------------------------------- #
# Cleaning steps
# --------------------------------------------------------------------------- #

class Cleaner:
	"""Apply rejection steps one by one and count what each one removes."""

	def __init__(self, df: pd.DataFrame) -> None:
		self.df = df
		self.steps: list[tuple[str, int, int]] = [("Lignes brutes", 0, len(df))]

	def reject(self, mask: pd.Series, reason: str) -> None:
		mask = mask.reindex(self.df.index, fill_value=False).astype(bool)
		self.df = self.df[~mask]
		self.steps.append((reason, int(mask.sum()), len(self.df)))


def reject_invalid_records(cleaner: Cleaner) -> None:
	cleaner.reject(normalise(cleaner.df["c_etat_valid"]) != "validées", "non validé")
	cleaner.reject(normalise(cleaner.df["c_etat"]) != "actif", "non actif")
	cleaner.reject(normalise(cleaner.df["c_etat_fonct"]) != "en fonctionnement", "pas en fonctionnement")
	cleaner.reject(normalise(cleaner.df["c_dae_mobile"]) == "t", "DAE mobile")

	df = cleaner.df
	lat = pd.to_numeric(df["c_lat_coor1"].str.replace(",", ".", regex=False), errors="coerce")
	lon = pd.to_numeric(df["c_long_coor1"].str.replace(",", ".", regex=False), errors="coerce")
	invalid = (
		lat.isna() | lon.isna()
		| ~lat.between(-90, 90) | ~lon.between(-180, 180)
		| ((lat == 0) & (lon == 0))
	)
	cleaner.df = df.assign(lat=lat, lon=lon)
	cleaner.reject(invalid, "coordonnées invalides")

	cleaner.reject(normalise(cleaner.df["c_doublon"]) == "t", "doublon signalé (c_doublon)")


def reject_spatial_duplicates(cleaner: Cleaner, radius_m: float) -> None:
	"""Merge records closer than ``radius_m`` that share a name or a SIREN."""
	df = cleaner.df
	reason = f"doublon spatial (< {radius_m:g} m)"
	if len(df) < 2:
		cleaner.reject(pd.Series(False, index=df.index), reason)
		return

	pairs = cKDTree(to_ecef(df["lat"].to_numpy(), df["lon"].to_numpy())).query_pairs(
		radius_m, output_type="ndarray"
	)
	names = normalise(df["c_nom"]).to_numpy()
	sirens = normalise(df["c_expt_siren"]).to_numpy()
	if len(pairs):
		i, j = pairs[:, 0], pairs[:, 1]
		same_name = (names[i] == names[j]) & (names[i] != "")
		same_siren = (sirens[i] == sirens[j]) & (sirens[i] != "")
		pairs = pairs[same_name | same_siren]

	n = len(df)
	edges = (np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])) if len(pairs) else ([], ([], []))
	_, groups = connected_components(coo_matrix(edges, shape=(n, n)), directed=False)

	# In each group, keep the most recently updated record (smallest gid on ties).
	ranking = pd.DataFrame(
		{
			"group": groups,
			"maj": pd.to_datetime(df["c_maj_don"], errors="coerce"),
			"gid": pd.to_numeric(df["gid"], errors="coerce"),
		},
		index=df.index,
	).sort_values(["group", "maj", "gid"], ascending=[True, False, True], na_position="last")
	kept = ranking.drop_duplicates("group").index
	cleaner.reject(pd.Series(~df.index.isin(kept), index=df.index), reason)


def reject_stacked_points(cleaner: Cleaner, min_stack: int) -> None:
	"""Reject groups of devices sharing the same point but not the same address."""
	df = cleaner.df
	point = df["lat"].round(STACK_ROUNDING).astype(str) + "," + df["lon"].round(STACK_ROUNDING).astype(str)
	address = normalise(df["c_adr_num"] + " " + df["c_adr_voie"] + " " + df["c_com_insee"])
	grouped = pd.DataFrame({"point": point, "address": address}).groupby("point")["address"]
	stacked = (grouped.transform("size") >= min_stack) & (grouped.transform("nunique") >= 2)
	cleaner.reject(stacked, f"géolocalisation empilée (>= {min_stack} DAE, adresses différentes)")


def is_24_7(df: pd.DataFrame) -> pd.Series:
	days = df["c_disp_j"].map(parse_pg_array)
	hours = df["c_disp_h"].map(parse_pg_array)
	all_week = days.map(lambda d: "7j/7" in d or WEEK_DAYS.issubset(d))
	all_day = hours.map(lambda h: "24h/24" in h)
	return all_week & all_day


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #

def print_summary(cleaner: Cleaner) -> None:
	print("\n=== Étapes de nettoyage ===")
	print(f"{'Étape':<60} {'retirées':>9} {'restantes':>10}")
	for reason, removed, remaining in cleaner.steps:
		print(f"{reason:<60} {removed:>9} {remaining:>10}")


def print_distributions(df: pd.DataFrame) -> None:
	print("\n=== Valeurs réelles des champs d'accès et de disponibilité ===")
	for column in ("c_acc", "c_disp_j", "c_disp_h"):
		print(f"\n-- {column}")
		print(df[column].value_counts(dropna=False).head(10).to_string())


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def clean_geodae(
	input_path: Path,
	output_path: Path,
	dup_radius_m: float = DEFAULT_DUP_RADIUS_M,
	min_stack: int = DEFAULT_MIN_STACK,
	show_distributions: bool = True,
) -> pd.DataFrame:
	cleaner = Cleaner(read_raw(input_path))
	reject_invalid_records(cleaner)
	reject_spatial_duplicates(cleaner, dup_radius_m)
	reject_stacked_points(cleaner, min_stack)

	df = cleaner.df
	clean = df.assign(
		c_lat_coor1=df["lat"], c_long_coor1=df["lon"], is_24_7=is_24_7(df)
	)[OUTPUT_COLUMNS]

	output_path.parent.mkdir(parents=True, exist_ok=True)
	clean.to_csv(output_path, index=False, encoding="utf-8")

	print_summary(cleaner)
	if show_distributions:
		print_distributions(df)
	print(f"\n{len(clean)} DAE écrits dans {output_path}")
	return clean


def main() -> None:
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
	parser.add_argument("output", nargs="?", type=Path, default=DEFAULT_OUTPUT)
	parser.add_argument(
		"--dup-radius", type=float, default=DEFAULT_DUP_RADIUS_M,
		help="distance max (m) entre deux doublons (défaut : %(default)s)",
	)
	parser.add_argument(
		"--min-stack", type=int, default=DEFAULT_MIN_STACK,
		help="nb min de DAE au même point pour suspecter un géocodage mairie (défaut : %(default)s)",
	)
	parser.add_argument("--quiet", action="store_true", help="ne pas afficher les distributions")
	args = parser.parse_args()

	clean_geodae(
		args.input, args.output,
		dup_radius_m=args.dup_radius, min_stack=args.min_stack,
		show_distributions=not args.quiet,
	)


if __name__ == "__main__":
	main()
