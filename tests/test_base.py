#
# openslide-python - Python bindings for the OpenSlide library
#
# Copyright (c) 2016-2023 Benjamin Gilbert
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

import ctypes
import unittest

from common import file_path

from openslide import ImageSlide, OpenSlide, lowlevel, open_slide


class TestLibrary(unittest.TestCase):
    def test_open_slide(self):
        with open_slide(file_path('boxes.tiff')) as osr:
            self.assertTrue(isinstance(osr, OpenSlide))
        with open_slide(file_path('boxes.png')) as osr:
            self.assertTrue(isinstance(osr, ImageSlide))

    def test_lowlevel_available(self):
        '''Ensure all exported functions have an 'available' attribute.'''
        for name in dir(lowlevel):
            # ignore classes and unexported functions
            if name.startswith('_') or name[0].isupper():
                continue
            # ignore random imports
            if hasattr(ctypes, name) or name in ('count', 'platform'):
                continue
            self.assertTrue(
                hasattr(getattr(lowlevel, name), 'available'),
                f'"{name}" missing "available" attribute',
            )
