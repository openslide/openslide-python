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

from functools import wraps
import os
from PIL import Image
import unittest

# PIL.Image cannot have zero width or height on Pillow 3.4.0 - 3.4.2
# https://github.com/python-pillow/Pillow/issues/2259
try:
    Image.new('RGBA', (1, 0))
    image_dimensions_cannot_be_zero = False
except ValueError:
    image_dimensions_cannot_be_zero = True


def file_path(name):
    return os.path.join(os.path.dirname(__file__), name)
