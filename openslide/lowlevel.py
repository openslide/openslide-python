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
import sys

_lib = cdll.LoadLibrary('libopenslide.so.0')

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

# resolve and return an OpenSlide function with the specified properties
def _func(name, restype, argtypes, errcheck=_check_error):
    func = getattr(_lib, name)
    func.argtypes = argtypes
    func.restype = restype
    if errcheck is not None:
        func.errcheck = errcheck
    return func

def _load_image(buf, size):
    '''buf can be a string, but should be a ctypes buffer to avoid an extra
    copy in the caller.'''
    # First reorder the bytes in a pixel from native-endian aRGB to
    # big-endian RGBa to work around limitations in RGBa loader
    rawmode = (sys.byteorder == 'little') and 'BGRA' or 'ARGB'
    buf = PIL.Image.frombuffer('RGBA', size, buf, 'raw', rawmode, 0,
            1).tostring()
    # Now load the image as RGBA, undoing premultiplication
    return PIL.Image.frombuffer('RGBA', size, buf, 'raw', 'RGBa', 0, 1)

can_open = _func('openslide_can_open', c_bool, [c_char_p], None)

open = _func('openslide_open', _OpenSlide, [c_char_p], _check_open)

close = _func('openslide_close', None, [_OpenSlide], None)

get_layer_count = _func('openslide_get_layer_count', c_int32, [_OpenSlide])

_get_layer_dimensions = _func('openslide_get_layer_dimensions', None,
        [_OpenSlide, c_int32, POINTER(c_int64), POINTER(c_int64)])
def get_layer_dimensions(slide, layer):
    w, h = c_int64(), c_int64()
    _get_layer_dimensions(slide, layer, byref(w), byref(h))
    return w.value, h.value

get_layer_downsample = _func('openslide_get_layer_downsample', c_double,
        [_OpenSlide, c_int32])

get_best_layer_for_downsample = \
        _func('openslide_get_best_layer_for_downsample', c_int32,
        [_OpenSlide, c_double])

_read_region = _func('openslide_read_region', None,
        [_OpenSlide, POINTER(c_uint32), c_int64, c_int64, c_int32, c_int64,
        c_int64])
def read_region(slide, x, y, layer, w, h):
    buf = create_string_buffer(w * h * 4)
    dest = cast(buf, POINTER(c_uint32))
    _read_region(slide, dest, x, y, layer, w, h)
    return _load_image(buf, (w, h))

get_error = _func('openslide_get_error', c_char_p, [_OpenSlide], None)

get_property_names = _func('openslide_get_property_names', POINTER(c_char_p),
        [_OpenSlide], _check_name_list)

get_property_value = _func('openslide_get_property_value', c_char_p,
        [_OpenSlide, c_char_p])

get_associated_image_names = _func('openslide_get_associated_image_names',
        POINTER(c_char_p), [_OpenSlide], _check_name_list)

_get_associated_image_dimensions = \
        _func('openslide_get_associated_image_dimensions', None,
        [_OpenSlide, c_char_p, POINTER(c_int64), POINTER(c_int64)])
def get_associated_image_dimensions(slide, name):
    w, h = c_int64(), c_int64()
    _get_associated_image_dimensions(slide, name, byref(w), byref(h))
    return w.value, h.value

_read_associated_image = _func('openslide_read_associated_image', None,
        [_OpenSlide, c_char_p, POINTER(c_uint32)])
def read_associated_image(slide, name):
    w, h = c_int64(), c_int64()
    _get_associated_image_dimensions(slide, name, byref(w), byref(h))
    buf = create_string_buffer(w.value * h.value * 4)
    dest = cast(buf, POINTER(c_uint32))
    _read_associated_image(slide, name, dest)
    return _load_image(buf, (w.value, h.value))
