#
# openslide-python - Python bindings for the OpenSlide library
#
# Copyright (c) 2016 Benjamin Gilbert
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of version 2.1 of the GNU Lesser General Public License
# as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library.  If not, see <https://www.gnu.org/licenses/>.
#

from __future__ import annotations

import unittest

from common import file_path
from PIL import Image

from openslide import ImageSlide, OpenSlide, lowlevel
from openslide.deepzoom import DeepZoomGenerator


class _Abstract:
    # nested class to prevent the test runner from finding it
    class BoxesDeepZoomTest(unittest.TestCase):
        CLASS: type | None = None
        FILENAME: str | None = None

        def setUp(self) -> None:
            assert self.CLASS is not None
            assert self.FILENAME is not None
            self.osr = self.CLASS(file_path(self.FILENAME))
            self.dz = DeepZoomGenerator(self.osr, 254, 1)

        def tearDown(self) -> None:
            self.osr.close()

        def test_repr(self) -> None:
            self.assertEqual(
                repr(self.dz),
                f'DeepZoomGenerator({self.osr!r}, tile_size=254, overlap=1, limit_bounds=False)',
            )

        def test_metadata(self) -> None:
            self.assertEqual(self.dz.level_count, 10)
            self.assertEqual(self.dz.tile_count, 11)
            self.assertEqual(
                self.dz.level_tiles,
                (
                    (1, 1),
                    (1, 1),
                    (1, 1),
                    (1, 1),
                    (1, 1),
                    (1, 1),
                    (1, 1),
                    (1, 1),
                    (1, 1),
                    (2, 1),
                ),
            )
            self.assertEqual(
                self.dz.level_dimensions,
                (
                    (1, 1),
                    (2, 1),
                    (3, 2),
                    (5, 4),
                    (10, 8),
                    (19, 16),
                    (38, 32),
                    (75, 63),
                    (150, 125),
                    (300, 250),
                ),
            )

        def test_get_tile(self) -> None:
            self.assertEqual(self.dz.get_tile(9, (1, 0)).size, (47, 250))

        def test_get_tile_matches_tile_dimensions(self) -> None:
            for level in range(self.dz.level_count):
                cols, rows = self.dz.level_tiles[level]
                for col in range(cols):
                    for row in range(rows):
                        self.assertEqual(
                            self.dz.get_tile(level, (col, row)).size,
                            self.dz.get_tile_dimensions(level, (col, row)),
                        )

        def test_tile_color_profile(self) -> None:
            if self.CLASS is OpenSlide and not lowlevel.read_icc_profile.available:
                self.skipTest('requires OpenSlide 4.0.0')
            self.assertEqual(len(self.dz.get_tile(9, (1, 0)).info['icc_profile']), 588)

        def test_get_tile_bad_level(self) -> None:
            self.assertRaises(ValueError, lambda: self.dz.get_tile(-1, (0, 0)))
            self.assertRaises(ValueError, lambda: self.dz.get_tile(10, (0, 0)))

        def test_get_tile_bad_address(self) -> None:
            self.assertRaises(ValueError, lambda: self.dz.get_tile(0, (-1, 0)))
            self.assertRaises(ValueError, lambda: self.dz.get_tile(0, (1, 0)))

        def test_get_tile_coordinates(self) -> None:
            self.assertEqual(
                self.dz.get_tile_coordinates(9, (1, 0)), ((253, 0), 0, (47, 250))
            )

        def test_get_tile_dimensions(self) -> None:
            self.assertEqual(self.dz.get_tile_dimensions(9, (1, 0)), (47, 250))

        def test_get_dzi(self) -> None:
            self.assertTrue(
                'http://schemas.microsoft.com/deepzoom/2008' in self.dz.get_dzi('jpeg')
            )


class TestSlideDeepZoom(_Abstract.BoxesDeepZoomTest):
    CLASS = OpenSlide
    FILENAME = 'boxes.tiff'


class TestImageDeepZoom(_Abstract.BoxesDeepZoomTest):
    CLASS = ImageSlide
    FILENAME = 'boxes.png'


class TestDeepZoomEdgeTileSizes(unittest.TestCase):
    def test_consistent_column_and_row_tile_sizes(self) -> None:
        # Downsampled multi-tile level where edge tiles have non-uniform
        # source aspect ratios (issue #111).
        img = Image.new('RGB', (1439, 1029))
        with ImageSlide(img) as osr:
            dz = DeepZoomGenerator(osr, tile_size=254, overlap=1)
            level = dz.level_count - 2  # 720x515 -> 3x3 tiles
            cols, rows = dz.level_tiles[level]
            col_widths: list[set[int]] = [set() for _ in range(cols)]
            row_heights: list[set[int]] = [set() for _ in range(rows)]
            for col in range(cols):
                for row in range(rows):
                    tile = dz.get_tile(level, (col, row))
                    expected = dz.get_tile_dimensions(level, (col, row))
                    self.assertEqual(tile.size, expected)
                    col_widths[col].add(tile.width)
                    row_heights[row].add(tile.height)
            for widths in col_widths:
                self.assertEqual(len(widths), 1)
            for heights in row_heights:
                self.assertEqual(len(heights), 1)
