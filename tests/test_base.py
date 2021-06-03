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
# along with this library; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import unittest

from openslide import ImageSlide, OpenSlide, open_slide

from . import file_path


class TestLibrary(unittest.TestCase):
    def test_open_slide(self):
        with open_slide(file_path('boxes.tiff')) as osr:
            self.assertTrue(isinstance(osr, OpenSlide))
        with open_slide(file_path('boxes.png')) as osr:
            self.assertTrue(isinstance(osr, ImageSlide))
