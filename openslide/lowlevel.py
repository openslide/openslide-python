#
# openslide-python - Python bindings for the OpenSlide library
#
# Copyright (c) 2010-2011 Carnegie Mellon University
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

from ctypes import *
from itertools import count
import PIL.Image
import struct
import sys

_lib = cdll.LoadLibrary('libopenslide.so.0')

PROPERTY_NAME_COMMENT          = 'openslide.comment'
PROPERTY_NAME_VENDOR           = 'openslide.vendor'
PROPERTY_NAME_QUICKHASH1       = 'openslide.quickhash-1'
PROPERTY_NAME_BACKGROUND_COLOR = 'openslide.background-color'

class OpenSlideError(Exception):
    pass

# validating class to make sure we correctly pass an OpenSlide handle
class _OpenSlide(c_void_p):
    @classmethod
    def from_param(cls, obj):
        if not obj:
            raise ValueError("Passing undefined slide object")
        if obj.__class__ != cls:
            raise ValueError("Not an OpenSlide reference")
        return super(_OpenSlide, cls).from_param(obj)

# check for errors opening an image file
def _check_open(result, func, args):
    if result.value is None:
        raise OpenSlideError("Could not open image file")
    return result

# check if the library got into an error state after each library call
def _check_error(result, func, args):
    err = get_error(args[0])
    if err is not None:
        raise OpenSlideError(err)
    return result

# Convert returned NULL-terminated string array into a list
def _check_name_list(result, func, args):
    _check_error(result, func, args)
    names = []
    for i in count():
        name = result[i]
        if not name:
            break
        names.append(name)
    return names

can_open = _lib.openslide_can_open
can_open.restype = c_int # c_bool
can_open.argtypes = [ c_char_p ]

open = _lib.openslide_open
open.restype = _OpenSlide
open.argtypes = [ c_char_p ]
open.errcheck = _check_open

close = _lib.openslide_close
close.restype = None
close.argtypes = [ _OpenSlide ]

get_layer_count = _lib.openslide_get_layer_count
get_layer_count.restype = c_int32
get_layer_count.argtypes = [ _OpenSlide ]
get_layer_count.errcheck = _check_error

_get_layer_dimensions = _lib.openslide_get_layer_dimensions
_get_layer_dimensions.restype = None
_get_layer_dimensions.argtypes = [ _OpenSlide, c_int32, POINTER(c_int64), POINTER(c_int64) ]
_get_layer_dimensions.errcheck = _check_error
def get_layer_dimensions(slide, layer):
    w, h = c_int64(), c_int64()
    _get_layer_dimensions(slide, layer, byref(w), byref(h))
    return w.value, h.value

get_layer_downsample = _lib.openslide_get_layer_downsample
get_layer_downsample.restype = c_double
get_layer_downsample.argtypes = [ _OpenSlide, c_int32 ]
get_layer_downsample.errcheck = _check_error

get_best_layer_for_downsample = _lib.openslide_get_best_layer_for_downsample
get_best_layer_for_downsample.restype = c_int32
get_best_layer_for_downsample.argtypes = [ _OpenSlide, c_double ]
get_best_layer_for_downsample.errcheck = _check_error

_read_region = _lib.openslide_read_region
_read_region.restype = None
_read_region.argtypes = [ _OpenSlide, POINTER(c_uint32), c_int64, c_int64, c_int32, c_int64, c_int64 ]
_read_region.errcheck = _check_error
def read_region(slide, x, y, layer, w, h):
    buf = create_string_buffer(w * h * 4)
    dest = cast(buf, POINTER(c_uint32))
    _read_region(slide, dest, x, y, layer, w, h)
    return _aRGB_to_RGBa(buf, (w, h))

get_error = _lib.openslide_get_error
get_error.restype = c_char_p
get_error.argtypes = [ _OpenSlide ]

get_property_names = _lib.openslide_get_property_names
get_property_names.restype = POINTER(c_char_p)
get_property_names.argtypes = [ _OpenSlide ]
get_property_names.errcheck = _check_name_list

get_property_value = _lib.openslide_get_property_value
get_property_value.restype = c_char_p
get_property_value.argtypes = [ _OpenSlide, c_char_p ]
get_property_value.errcheck = _check_error

get_associated_image_names = _lib.openslide_get_associated_image_names
get_associated_image_names.restype = POINTER(c_char_p)
get_associated_image_names.argtypes = [ _OpenSlide ]
get_associated_image_names.errcheck = _check_name_list

_get_associated_image_dimensions = _lib.openslide_get_associated_image_dimensions
_get_associated_image_dimensions.restype = None
_get_associated_image_dimensions.argtypes = [ _OpenSlide, c_char_p, POINTER(c_int64), POINTER(c_int64) ]
_get_associated_image_dimensions.errcheck = _check_error
def get_associated_image_dimensions(slide, name):
    w, h = c_int64(), c_int64()
    _get_associated_image_dimensions(slide, name, byref(w), byref(h))
    return w.value, h.value

_read_associated_image = _lib.openslide_read_associated_image
_read_associated_image.restype = None
_read_associated_image.argtypes = [ _OpenSlide, c_char_p, POINTER(c_uint32) ]
_read_associated_image.errcheck = _check_error
def read_associated_image(slide, name):
    w, h = c_int64(), c_int64()
    _get_associated_image_dimensions(slide, name, byref(w), byref(h))
    buf = create_string_buffer(w.value * h.value * 4)
    dest = cast(buf, POINTER(c_uint32))
    _read_associated_image(slide, name, dest)
    return _aRGB_to_RGBa(buf, (w.value, h.value))

# repack buffer from native-endian aRGB to big-endian RGBa and return PIL.Image
_rawmode = (sys.byteorder == 'little') and 'BGRA' or 'ARGB'
def _aRGB_to_RGBa(buf, size):
    i = PIL.Image.frombuffer('RGBA', size, buf.raw, 'raw', _rawmode, 0, 1)
    return PIL.Image.frombuffer('RGBA', size, i.tostring(), 'raw', 'RGBa', 0, 1)
