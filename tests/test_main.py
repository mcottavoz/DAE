import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from shapely.geometry import Point, Polygon

from src.main import create_map, load_dae_points, load_population_cells, population_color


class MapTests(unittest.TestCase):
	def setUp(self):
		self.geometry = Polygon(
			[(-1.2, 46.1), (-1.1, 46.1), (-1.1, 46.2), (-1.2, 46.2)]
		)

	def test_load_dae_points_keeps_only_points_in_geometry(self):
		with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as csv_file:
			csv_file.write(
				"c_lat_coor1,c_long_coor1\n"
				"46.15,-1.15\n"
				"46.30,-1.15\n"
			)
			csv_path = Path(csv_file.name)

		try:
			points = load_dae_points(csv_path, self.geometry)
		finally:
			csv_path.unlink()

		self.assertEqual(points, [Point(-1.15, 46.15)])

	def test_map_contains_one_dae_marker(self):
		with patch("src.main.get_place_geometry", return_value=self.geometry):
			map_view = create_map(dae_points=[self.geometry.representative_point()])

		clusters = [
			child
			for child in map_view._children.values()
			if child.__class__.__name__ == "MarkerCluster"
		]
		markers = [
			child for child in clusters[0]._children.values() if child.__class__.__name__ == "Marker"
		]
		self.assertEqual(len(markers), 1)

	def test_map_groups_multiple_dae_markers(self):
		dae_points = [
			self.geometry.representative_point(),
			self.geometry.representative_point(),
		]
		with patch("src.main.get_place_geometry", return_value=self.geometry):
			map_view = create_map(dae_points=dae_points)

		cluster = next(
			child
			for child in map_view._children.values()
			if child.__class__.__name__ == "MarkerCluster"
		)
		markers = [
			child for child in cluster._children.values() if child.__class__.__name__ == "Marker"
		]
		self.assertEqual(len(markers), 2)

	def test_map_loads_csv_points_and_filters_outside_points(self):
		with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as csv_file:
			csv_file.write(
				"c_lat_coor1,c_long_coor1\n"
				"46.15,-1.15\n"
				"46.30,-1.15\n"
			)
			csv_path = Path(csv_file.name)

		try:
			with patch("src.main.get_place_geometry", return_value=self.geometry):
				map_view = create_map(dae_file=csv_path)
		finally:
			csv_path.unlink()

		cluster = next(
			child
			for child in map_view._children.values()
			if child.__class__.__name__ == "MarkerCluster"
		)
		markers = [
			child for child in cluster._children.values() if child.__class__.__name__ == "Marker"
		]
		self.assertEqual(len(markers), 1)

	def test_load_population_cells_reads_square_coordinates(self):
		with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as csv_file:
			csv_file.write(
				"lon_bas_gauche,lat_bas_gauche,lon_haut_droit,lat_haut_droit,ind\n"
				"-1.15,46.15,-1.14,46.16,42\n"
				"-1.50,46.50,-1.49,46.51,99\n"
			)
			csv_path = Path(csv_file.name)

		try:
			cells = load_population_cells(csv_path, self.geometry)
		finally:
			csv_path.unlink()

		populated_cells = [cell for cell in cells if cell["population"] == 42]
		empty_cells = [cell for cell in cells if cell["population"] == 0]
		self.assertEqual(len(populated_cells), 1)
		self.assertGreater(len(empty_cells), 0)
		self.assertEqual(populated_cells[0]["bounds"], (-1.15, 46.15, -1.14, 46.16))

	def test_load_population_cells_excludes_square_outside_geometry(self):
		with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as csv_file:
			csv_file.write(
				"lon_bas_gauche,lat_bas_gauche,lon_haut_droit,lat_haut_droit,ind\n"
				"-1.15,46.15,-1.14,46.16,42\n"
				"-1.15,46.19,-1.14,46.21,42\n"
			)
			csv_path = Path(csv_file.name)

		try:
			cells = load_population_cells(csv_path, self.geometry)
		finally:
			csv_path.unlink()

		self.assertEqual(len([cell for cell in cells if cell["population"] == 42]), 1)
		self.assertTrue(all(cell["bounds"][3] <= 46.2 for cell in cells))

	def test_population_colors_distinguish_population_levels(self):
		thresholds = (50, 100, 200)

		self.assertEqual(population_color(20, thresholds), "#2ca25f")
		self.assertEqual(population_color(75, thresholds), "#f1c40f")
		self.assertEqual(population_color(150, thresholds), "#f07818")
		self.assertEqual(population_color(250, thresholds), "#d73027")

	def test_map_contains_population_layer_and_square(self):
		with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as csv_file:
			csv_file.write(
				"lon_bas_gauche,lat_bas_gauche,lon_haut_droit,lat_haut_droit,ind\n"
				"-1.15,46.15,-1.14,46.16,42\n"
			)
			population_path = Path(csv_file.name)

		try:
			with patch("src.main.get_place_geometry", return_value=self.geometry):
				map_view = create_map(
					dae_points=[],
					population_file=population_path,
				)
		finally:
			population_path.unlink()

		population_layer = next(
			child
			for child in map_view._children.values()
			if child.__class__.__name__ == "FeatureGroup"
		)
		polygons = [
			child
			for child in population_layer._children.values()
			if child.__class__.__name__ == "Polygon"
		]
		self.assertEqual(len(polygons), 1)
		self.assertTrue(
			any(child.__class__.__name__ == "LayerControl" for child in map_view._children.values())
		)

	def test_map_contains_osm_geometry_layer(self):
		with patch("src.main.get_place_geometry", return_value=self.geometry):
			map_view = create_map(dae_points=[])

		geometry_layer = next(
			child
			for child in map_view._children.values()
			if child.__class__.__name__ == "GeoJson"
		)
		self.assertEqual(geometry_layer.layer_name, "Limite géométrique OSM")

	def test_map_crosses_missing_population_square(self):
		with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as csv_file:
			csv_file.write(
				"lon_bas_gauche,lat_bas_gauche,lon_haut_droit,lat_haut_droit,ind\n"
				"-1.15,46.15,-1.14,46.16,42\n"
				"-1.13,46.15,-1.12,46.16,42\n"
			)
			population_path = Path(csv_file.name)

		try:
			with patch("src.main.get_place_geometry", return_value=self.geometry):
				map_view = create_map(
					dae_points=[],
					population_file=population_path,
				)
		finally:
			population_path.unlink()

		population_layer = next(
			child
			for child in map_view._children.values()
			if child.__class__.__name__ == "FeatureGroup"
		)
		lines = [
			child
			for child in population_layer._children.values()
			if child.__class__.__name__ == "PolyLine"
		]
		self.assertGreaterEqual(len(lines), 2)
		self.assertEqual(len(lines) % 2, 0)

	def test_map_does_not_cross_present_zero_population_square(self):
		with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as csv_file:
			csv_file.write(
				"lon_bas_gauche,lat_bas_gauche,lon_haut_droit,lat_haut_droit,ind\n"
				"-1.15,46.15,-1.14,46.16,0\n"
			)
			population_path = Path(csv_file.name)

		try:
			with patch("src.main.get_place_geometry", return_value=self.geometry):
				map_view = create_map(dae_points=[], population_file=population_path)
		finally:
			population_path.unlink()

		population_layer = next(
			child
			for child in map_view._children.values()
			if child.__class__.__name__ == "FeatureGroup"
		)
		lines = [
			child
			for child in population_layer._children.values()
			if child.__class__.__name__ == "PolyLine"
		]
		self.assertEqual(len(lines), 0)
