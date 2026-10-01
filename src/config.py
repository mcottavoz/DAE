"""Constantes et valeurs par défaut du projet."""

from pathlib import Path

BASE_DIR = Path(__file__).parent

DEFAULT_PLACE = "La Rochelle, France"

DEFAULT_DAE_FILE = BASE_DIR / "Fichier_csv" / "geodae_larochelle.csv"

DEFAULT_POPULATION_FILE = (
    BASE_DIR / "Fichier_csv" / "carreaux_200m_la_rochelle_coord.csv"
)

DEFAULT_OUTPUT_FILE = Path("la_rochelle.html")

# Zoom initial (écrasé ensuite par fit_bounds)
DEFAULT_ZOOM = 13

# Couleurs des quatre niveaux de population (du plus faible au plus fort)
POPULATION_COLORS = ("#2ca25f", "#f1c40f", "#f07818", "#d73027")