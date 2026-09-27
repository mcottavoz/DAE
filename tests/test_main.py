import random
import unittest
from unittest.mock import patch

from shapely.geometry import Polygon

from src.main import create_map, random_point_in_geometry


class MapTests(unittest.TestCase):
	def setUp(self):
		self.geometry = Polygon(
			[(-1.2, 46.1), (-1.1, 46.1), (-1.1, 46.2), (-1.2, 46.2)]
		)

	def test_random_point_is_inside_place_geometry(self):
		point = random_point_in_geometry(self.geometry, random.Random(42))

		self.assertTrue(self.geometry.contains(point))

	def test_map_contains_one_dae_marker(self):
		with patch("src.main.get_place_geometry", return_value=self.geometry):
			map_view = create_map(seed=42, dae_count=1)

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

	def test_map_has_five_demo_dae_by_default(self):
		with patch("src.main.get_place_geometry", return_value=self.geometry):
			map_view = create_map(seed=42)

		cluster = next(
			child
			for child in map_view._children.values()
			if child.__class__.__name__ == "MarkerCluster"
		)
		markers = [
			child for child in cluster._children.values() if child.__class__.__name__ == "Marker"
		]
		self.assertEqual(len(markers), 5)
