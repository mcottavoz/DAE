import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from shapely.geometry import Point, Polygon

from src.main import create_map, load_dae_points


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
