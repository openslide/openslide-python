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

import openslide
from openslide import open_slide, OpenSlide, ImageSlide
import sys
import unittest

from . import file_path

# Tests should be written to be compatible with Python 2.6 unittest.

class TestLibrary(unittest.TestCase):
    def test_version(self):
        string = unicode if sys.version[0] == '2' else str
        self.assertTrue(isinstance(openslide.__version__, string))
        self.assertTrue(isinstance(openslide.__library_version__, string))

    def test_open_slide(self):
        with open_slide(file_path('boxes.tiff')) as osr:
            self.assertTrue(isinstance(osr, OpenSlide))
        with open_slide(file_path('boxes.png')) as osr:
            self.assertTrue(isinstance(osr, ImageSlide))
