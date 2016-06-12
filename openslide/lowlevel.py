#
# openslide-python - Python bindings for the OpenSlide library
#
# Copyright (c) 2010-2013 Carnegie Mellon University
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

"""
Low-level interface to the OpenSlide library.

Most users should use the openslide.OpenSlide class rather than this
module.

This module provides nearly direct equivalents to the OpenSlide C API.
(As an implementation detail, conversion of premultiplied image data
returned by OpenSlide into a non-premultiplied PIL.Image happens here
rather than in the high-level interface.)
"""

from __future__ import division
from ctypes import *
from itertools import count
import PIL.Image
import platform
import sys

if platform.system() == 'Windows':
    _lib = cdll.LoadLibrary('libopenslide-0.dll')
elif platform.system() == 'Darwin':
    try:
        _lib = cdll.LoadLibrary('libopenslide.0.dylib')
    except OSError:
        # MacPorts doesn't add itself to the dyld search path, but
        # does add itself to the find_library() search path
        # (DEFAULT_LIBRARY_FALLBACK in ctypes.macholib.dyld) on
        # Python 2.6 and 2.7.  Python 3 users on MacPorts should add
        # the MacPorts lib directory to DYLD_LIBRARY_PATH.
        import ctypes.util
        _lib = ctypes.util.find_library('openslide')
        if _lib is None:
            raise ImportError("Couldn't locate OpenSlide dylib.  " +
                    "Is OpenSlide installed?")
        _lib = cdll.LoadLibrary(_lib)
else:
    _lib = cdll.LoadLibrary('libopenslide.so.0')

try:
    from . import _convert
    def _load_image(buf, size):
        '''buf must be a mutable buffer.'''
        _convert.argb2rgba(buf)
        return PIL.Image.frombuffer('RGBA', size, buf, 'raw', 'RGBA', 0, 1)
except ImportError:
    def _load_image(buf, size):
        '''buf must be a buffer.'''

        # Load entire buffer at once if possible
        MAX_PIXELS_PER_LOAD = (1 << 29) - 1
        # Otherwise, use chunks smaller than the maximum to reduce memory
        # requirements
        PIXELS_PER_LOAD = 1 << 26

        def do_load(buf, size):
            '''buf can be a string, but should be a ctypes buffer to avoid an
            extra copy in the caller.'''
            # First reorder the bytes in a pixel from native-endian aRGB to
            # big-endian RGBa to work around limitations in RGBa loader
            rawmode = (sys.byteorder == 'little') and 'BGRA' or 'ARGB'
            buf = PIL.Image.frombuffer('RGBA', size, buf, 'raw', rawmode, 0, 1)
            # Image.tobytes() is named tostring() in Pillow 1.x and PIL
            buf = (getattr(buf, 'tobytes', None) or buf.tostring)()
            # Now load the image as RGBA, undoing premultiplication
            return PIL.Image.frombuffer('RGBA', size, buf, 'raw', 'RGBa', 0, 1)

        # Fast path for small buffers
        w, h = size
        if w * h <= MAX_PIXELS_PER_LOAD:
            return do_load(buf, size)

        # Load in chunks to avoid OverflowError in PIL.Image.frombuffer()
        # https://github.com/python-pillow/Pillow/issues/1475
        if w > PIXELS_PER_LOAD:
            # We could support this, but it seems like overkill
            raise ValueError('Width %d is too large (maximum %d)' %
                    (w, PIXELS_PER_LOAD))
        rows_per_load = PIXELS_PER_LOAD // w
        img = PIL.Image.new('RGBA', (w, h))
        for y in range(0, h, rows_per_load):
            rows = min(h - y, rows_per_load)
            if sys.version[0] == '2':
                chunk = buffer(buf, 4 * y * w, 4 * rows * w)
            else:
                # PIL.Image.frombuffer() won't take a memoryview or
                # bytearray, so we can't avoid copying
                chunk = memoryview(buf)[y * w:(y + rows) * w].tobytes()
            img.paste(do_load(chunk, (w, rows)), (0, y))
        return img

class OpenSlideError(Exception):
    """An error produced by the OpenSlide library.

    Import this from openslide rather than from openslide.lowlevel.
    """

class OpenSlideUnsupportedFormatError(OpenSlideError):
    """OpenSlide does not support the requested file.

    Import this from openslide rather than from openslide.lowlevel.
    """

class _OpenSlide(object):
    """Wrapper class to make sure we correctly pass an OpenSlide handle."""

    def __init__(self, ptr):
        self._as_parameter_ = ptr
        self._valid = True
        # Retain a reference to close() to avoid GC problems during
        # interpreter shutdown
        self._close = close

    def __del__(self):
        if self._valid:
            self._close(self)

    def invalidate(self):
        self._valid = False

    @classmethod
    def from_param(cls, obj):
        if obj.__class__ != cls:
            raise ValueError("Not an OpenSlide reference")
        if not obj._as_parameter_:
            raise ValueError("Passing undefined slide object")
        if not obj._valid:
            raise ValueError("Passing closed slide object")
        return obj

class _utf8_p(object):
    """Wrapper class to convert string arguments to bytes."""

    if sys.version[0] == '2':
        _bytes_type = str
        _str_type = unicode
    else:
        _bytes_type = bytes
        _str_type = str

    @classmethod
    def from_param(cls, obj):
        if isinstance(obj, cls._bytes_type):
            return obj
        elif isinstance(obj, cls._str_type):
            return obj.encode('UTF-8')
        else:
            raise TypeError('Incorrect type')

# check for errors opening an image file and wrap the resulting handle
def _check_open(result, _func, _args):
    if result is None:
        raise OpenSlideUnsupportedFormatError(
                "Unsupported or missing image file")
    slide = _OpenSlide(c_void_p(result))
    err = get_error(slide)
    if err is not None:
        raise OpenSlideError(err)
    return slide

# prevent further operations on slide handle after it is closed
def _check_close(_result, _func, args):
    args[0].invalidate()

# Convert returned byte array, if present, into a string
def _check_string(result, func, _args):
    if func.restype is c_char_p and result is not None:
        return result.decode('UTF-8', 'replace')
    else:
        return result

# check if the library got into an error state after each library call
def _check_error(result, func, args):
    err = get_error(args[0])
    if err is not None:
        raise OpenSlideError(err)
    return _check_string(result, func, args)

# Convert returned NULL-terminated char** into a list of strings
def _check_name_list(result, func, args):
    _check_error(result, func, args)
    names = []
    for i in count():
        name = result[i]
        if not name:
            break
        names.append(name.decode('UTF-8', 'replace'))
    return names

# resolve and return an OpenSlide function with the specified properties
def _func(name, restype, argtypes, errcheck=_check_error):
    func = getattr(_lib, name)
    func.argtypes = argtypes
    func.restype = restype
    if errcheck is not None:
        func.errcheck = errcheck
    return func

try:
    detect_vendor = _func('openslide_detect_vendor', c_char_p, [_utf8_p],
            _check_string)
except AttributeError:
    raise OpenSlideError('OpenSlide >= 3.4.0 required')

open = _func('openslide_open', c_void_p, [_utf8_p], _check_open)

close = _func('openslide_close', None, [_OpenSlide], _check_close)

get_level_count = _func('openslide_get_level_count', c_int32, [_OpenSlide])

_get_level_dimensions = _func('openslide_get_level_dimensions', None,
        [_OpenSlide, c_int32, POINTER(c_int64), POINTER(c_int64)])
def get_level_dimensions(slide, level):
    w, h = c_int64(), c_int64()
    _get_level_dimensions(slide, level, byref(w), byref(h))
    return w.value, h.value

get_level_downsample = _func('openslide_get_level_downsample', c_double,
        [_OpenSlide, c_int32])

get_best_level_for_downsample = \
        _func('openslide_get_best_level_for_downsample', c_int32,
        [_OpenSlide, c_double])

_read_region = _func('openslide_read_region', None,
        [_OpenSlide, POINTER(c_uint32), c_int64, c_int64, c_int32, c_int64,
        c_int64])
def read_region(slide, x, y, level, w, h):
    if w < 0 or h < 0:
        # OpenSlide would catch this, but not before we tried to allocate
        # a negative-size buffer
        raise OpenSlideError(
                "negative width (%d) or negative height (%d) not allowed" % (
                w, h))
    if w == 0 or h == 0:
        # PIL.Image.frombuffer() would raise an exception
        return PIL.Image.new('RGBA', (w, h))
    buf = (w * h * c_uint32)()
    _read_region(slide, buf, x, y, level, w, h)
    return _load_image(buf, (w, h))

get_error = _func('openslide_get_error', c_char_p, [_OpenSlide], _check_string)

get_property_names = _func('openslide_get_property_names', POINTER(c_char_p),
        [_OpenSlide], _check_name_list)

get_property_value = _func('openslide_get_property_value', c_char_p,
        [_OpenSlide, _utf8_p])

get_associated_image_names = _func('openslide_get_associated_image_names',
        POINTER(c_char_p), [_OpenSlide], _check_name_list)

_get_associated_image_dimensions = \
        _func('openslide_get_associated_image_dimensions', None,
        [_OpenSlide, _utf8_p, POINTER(c_int64), POINTER(c_int64)])
def get_associated_image_dimensions(slide, name):
    w, h = c_int64(), c_int64()
    _get_associated_image_dimensions(slide, name, byref(w), byref(h))
    return w.value, h.value

_read_associated_image = _func('openslide_read_associated_image', None,
        [_OpenSlide, _utf8_p, POINTER(c_uint32)])
def read_associated_image(slide, name):
    w, h = get_associated_image_dimensions(slide, name)
    buf = (w * h * c_uint32)()
    _read_associated_image(slide, name, buf)
    return _load_image(buf, (w, h))

get_version = _func('openslide_get_version', c_char_p, [], _check_string)
