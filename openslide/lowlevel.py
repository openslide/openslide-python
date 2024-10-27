#
# openslide-python - Python bindings for the OpenSlide library
#
# Copyright (c) 2010-2013 Carnegie Mellon University
# Copyright (c) 2016-2024 Benjamin Gilbert
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

from __future__ import annotations

from ctypes import (
    CDLL,
    POINTER,
    _Pointer,
    byref,
    c_char,
    c_char_p,
    c_double,
    c_int32,
    c_int64,
    c_size_t,
    c_uint32,
    c_void_p,
    cdll,
)
from itertools import count
import os
import platform
from typing import TYPE_CHECKING, Any, Callable, Protocol, TypeVar, cast

from PIL import Image

from . import _convert

if TYPE_CHECKING:
    # Python 3.10+
    from typing import ParamSpec, TypeAlias

    from _convert import _Buffer


def _load_library() -> CDLL:
    try:
        import openslide_bin

        return openslide_bin.libopenslide1
    except (AttributeError, ModuleNotFoundError):
        pass

    def try_load(names: list[str]) -> CDLL:
        try:
            return cdll.LoadLibrary(names[0])
        except OSError:
            remaining = names[1:]
            if remaining:
                # handle recursively so implicit exception chaining captures
                # all the failures
                return try_load(remaining)
            else:
                raise

    if platform.system() == 'Windows':
        try:
            return try_load(['libopenslide-1.dll', 'libopenslide-0.dll'])
        except FileNotFoundError as exc:
            raise ModuleNotFoundError(
                "Couldn't locate OpenSlide DLL. "
                "Try `pip install openslide-bin`, "
                "or if you're using an OpenSlide binary package, "
                "ensure you've called os.add_dll_directory(). "
                "https://openslide.org/api/python/#installing"
            ) from exc
    elif platform.system() == 'Darwin':
        try:
            return try_load(['libopenslide.1.dylib', 'libopenslide.0.dylib'])
        except OSError as exc:
            # MacPorts doesn't add itself to the dyld search path, but
            # does add itself to the find_library() search path
            # (DEFAULT_LIBRARY_FALLBACK in ctypes.macholib.dyld).
            import ctypes.util

            lib = ctypes.util.find_library('openslide')
            if lib is None:
                raise ModuleNotFoundError(
                    "Couldn't locate OpenSlide dylib. "
                    "Try `pip install openslide-bin`. "
                    "https://openslide.org/api/python/#installing"
                ) from exc
            return cdll.LoadLibrary(lib)
    else:
        try:
            return try_load(['libopenslide.so.1', 'libopenslide.so.0'])
        except OSError as exc:
            raise ModuleNotFoundError(
                "Couldn't locate OpenSlide shared library. "
                "Try `pip install openslide-bin`. "
                "https://openslide.org/api/python/#installing"
            ) from exc


_lib = _load_library()


class OpenSlideError(Exception):
    """An error produced by the OpenSlide library.

    Import this from openslide rather than from openslide.lowlevel.
    """


class OpenSlideVersionError(OpenSlideError):
    """This version of OpenSlide does not support the requested functionality.

    Import this from openslide rather than from openslide.lowlevel.
    """

    def __init__(self, minimum_version: str):
        super().__init__(f'OpenSlide >= {minimum_version} required')
        self.minimum_version = minimum_version


class OpenSlideUnsupportedFormatError(OpenSlideError):
    """OpenSlide does not support the requested file.

    Import this from openslide rather than from openslide.lowlevel.
    """


class _OpenSlide:
    """Wrapper class to make sure we correctly pass an OpenSlide handle."""

    def __init__(self, ptr: c_void_p):
        self._as_parameter_ = ptr
        self._valid = True
        # Retain a reference to close() to avoid GC problems during
        # interpreter shutdown
        self._close = close

    def __del__(self) -> None:
        if self._valid:
            self._close(self)

    def invalidate(self) -> None:
        self._valid = False

    @classmethod
    def from_param(cls, obj: _OpenSlide) -> _OpenSlide:
        if obj.__class__ != cls:
            raise ValueError("Not an OpenSlide reference")
        if not obj._as_parameter_:
            raise ValueError("Passing undefined slide object")
        if not obj._valid:
            raise ValueError("Passing closed slide object")
        return obj


class _OpenSlideCache:
    """Wrapper class to make sure we correctly pass an OpenSlide cache."""

    def __init__(self, ptr: c_void_p):
        self._as_parameter_ = ptr
        # Retain a reference to cache_release() to avoid GC problems during
        # interpreter shutdown
        self._cache_release = cache_release

    def __del__(self) -> None:
        self._cache_release(self)

    @classmethod
    def from_param(cls, obj: _OpenSlideCache) -> _OpenSlideCache:
        if obj.__class__ != cls:
            raise ValueError("Not an OpenSlide cache reference")
        if not obj._as_parameter_:
            raise ValueError("Passing undefined cache object")
        return obj


if TYPE_CHECKING:
    # Python 3.10+
    Filename: TypeAlias = str | bytes | os.PathLike[Any]


class _filename_p:
    """Wrapper class to convert filename arguments to bytes."""

    @classmethod
    def from_param(cls, obj: Filename) -> bytes:
        # fspath and fsencode raise TypeError on unexpected types
        if platform.system() == 'Windows':
            # OpenSlide 4.0.0+ requires UTF-8 on Windows
            obj = os.fspath(obj)
            if isinstance(obj, str):
                return obj.encode('UTF-8')
            else:
                return obj
        else:
            return os.fsencode(obj)


class _utf8_p:
    """Wrapper class to convert string arguments to bytes."""

    @classmethod
    def from_param(cls, obj: str | bytes) -> bytes:
        if isinstance(obj, bytes):
            return obj
        elif isinstance(obj, str):
            return obj.encode('UTF-8')
        else:
            raise TypeError('Incorrect type')


class _size_t:
    """Wrapper class to convert size_t arguments to c_size_t."""

    @classmethod
    def from_param(cls, obj: int) -> c_size_t:
        if not isinstance(obj, int):
            raise TypeError('Incorrect type')
        if obj < 0:
            raise ValueError('Value out of range')
        return c_size_t(obj)


def _load_image(buf: _Buffer, size: tuple[int, int]) -> Image.Image:
    '''buf must be a mutable buffer.'''
    _convert.argb2rgba(buf)
    return Image.frombuffer('RGBA', size, buf, 'raw', 'RGBA', 0, 1)


# check for errors opening an image file and wrap the resulting handle
def _check_open(result: int | None, _func: Any, _args: Any) -> _OpenSlide:
    if result is None:
        raise OpenSlideUnsupportedFormatError("Unsupported or missing image file")
    slide = _OpenSlide(c_void_p(result))
    err = get_error(slide)
    if err is not None:
        raise OpenSlideError(err)
    return slide


# prevent further operations on slide handle after it is closed
def _check_close(_result: Any, _func: Any, args: tuple[_OpenSlide]) -> None:
    args[0].invalidate()


# wrap the handle returned when creating a cache
def _check_cache_create(result: int, _func: Any, _args: Any) -> _OpenSlideCache:
    return _OpenSlideCache(c_void_p(result))


# Convert returned byte array, if present, into a string
def _check_string(result: Any, func: _CTypesFunc[..., Any], _args: Any) -> Any:
    if func.restype is c_char_p and result is not None:
        return result.decode('UTF-8', 'replace')
    else:
        return result


# check if the library got into an error state after each library call
def _check_error(result: Any, func: Any, args: tuple[Any, ...]) -> Any:
    assert isinstance(args[0], _OpenSlide)
    err = get_error(args[0])
    if err is not None:
        raise OpenSlideError(err)
    return _check_string(result, func, args)


# Convert returned NULL-terminated char** into a list of strings
def _check_name_list(result: _Pointer[c_char_p], func: Any, args: Any) -> list[str]:
    _check_error(result, func, args)
    names = []
    for i in count():
        name = result[i]
        if not name:
            break
        names.append(name.decode('UTF-8', 'replace'))
    return names


class _FunctionUnavailable:
    '''Standin for a missing optional function.  Fails when called.'''

    def __init__(self, minimum_version: str):
        self._minimum_version = minimum_version
        # allow checking for availability without calling the function
        self.available = False

    def __call__(self, *_args: Any) -> Any:
        raise OpenSlideVersionError(self._minimum_version)


# gate runtime code that requires ParamSpec, Python 3.10+
if TYPE_CHECKING:
    _P = ParamSpec('_P')
    _T = TypeVar('_T', covariant=True)

    class _Func(Protocol[_P, _T]):
        available: bool

        def __call__(self, *args: _P.args) -> _T: ...

    class _CTypesFunc(_Func[_P, _T]):
        restype: type | None
        argtypes: list[type]
        errcheck: _ErrCheck

    _ErrCheck: TypeAlias = (
        Callable[[Any, _CTypesFunc[..., Any], tuple[Any, ...]], Any] | None
    )


# resolve and return an OpenSlide function with the specified properties
def _func(
    name: str,
    restype: type | None,
    argtypes: list[type],
    errcheck: _ErrCheck = _check_error,
    minimum_version: str | None = None,
) -> _Func[_P, _T]:
    try:
        func: _CTypesFunc[_P, _T] = getattr(_lib, name)
    except AttributeError:
        if minimum_version is None:
            raise
        else:
            return _FunctionUnavailable(minimum_version)
    func.argtypes = argtypes
    func.restype = restype
    if errcheck is not None:
        func.errcheck = errcheck
    func.available = True
    return func


def _wraps_funcs(
    wrapped: list[_Func[..., Any]]
) -> Callable[[Callable[_P, _T]], _Func[_P, _T]]:
    def decorator(fn: Callable[_P, _T]) -> _Func[_P, _T]:
        if TYPE_CHECKING:
            # requires ParamSpec, Python 3.10+
            f = cast(_Func[_P, _T], fn)
        else:
            f = fn
        f.available = True
        for w in wrapped:
            f.available = f.available and w.available
        return f

    return decorator


try:
    detect_vendor: _Func[[Filename], str] = _func(
        'openslide_detect_vendor', c_char_p, [_filename_p], _check_string
    )
except AttributeError:
    raise OpenSlideVersionError('3.4.0')

open: _Func[[Filename], _OpenSlide] = _func(
    'openslide_open', c_void_p, [_filename_p], _check_open
)

close: _Func[[_OpenSlide], None] = _func(
    'openslide_close', None, [_OpenSlide], _check_close
)

get_level_count: _Func[[_OpenSlide], int] = _func(
    'openslide_get_level_count', c_int32, [_OpenSlide]
)

_get_level_dimensions: _Func[
    [_OpenSlide, int, _Pointer[c_int64], _Pointer[c_int64]], None
] = _func(
    'openslide_get_level_dimensions',
    None,
    [_OpenSlide, c_int32, POINTER(c_int64), POINTER(c_int64)],
)


@_wraps_funcs([_get_level_dimensions])
def get_level_dimensions(slide: _OpenSlide, level: int) -> tuple[int, int]:
    w, h = c_int64(), c_int64()
    _get_level_dimensions(slide, level, byref(w), byref(h))
    return w.value, h.value


get_level_downsample: _Func[[_OpenSlide, int], float] = _func(
    'openslide_get_level_downsample', c_double, [_OpenSlide, c_int32]
)

get_best_level_for_downsample: _Func[[_OpenSlide, float], int] = _func(
    'openslide_get_best_level_for_downsample', c_int32, [_OpenSlide, c_double]
)

_read_region: _Func[[_OpenSlide, _Pointer[c_uint32], int, int, int, int, int], None] = (
    _func(
        'openslide_read_region',
        None,
        [_OpenSlide, POINTER(c_uint32), c_int64, c_int64, c_int32, c_int64, c_int64],
    )
)


@_wraps_funcs([_read_region])
def read_region(
    slide: _OpenSlide, x: int, y: int, level: int, w: int, h: int
) -> Image.Image:
    if w < 0 or h < 0:
        # OpenSlide would catch this, but not before we tried to allocate
        # a negative-size buffer
        raise OpenSlideError(
            "negative width (%d) or negative height (%d) not allowed" % (w, h)
        )
    if w == 0 or h == 0:
        # Image.frombuffer() would raise an exception
        return Image.new('RGBA', (w, h))
    buf = (w * h * c_uint32)()
    _read_region(slide, buf, x, y, level, w, h)
    return _load_image(buf, (w, h))


get_icc_profile_size: _Func[[_OpenSlide], int] = _func(
    'openslide_get_icc_profile_size',
    c_int64,
    [_OpenSlide],
    minimum_version='4.0.0',
)

_read_icc_profile: _Func[[_OpenSlide, _Pointer[c_char]], None] = _func(
    'openslide_read_icc_profile',
    None,
    [_OpenSlide, POINTER(c_char)],
    minimum_version='4.0.0',
)


@_wraps_funcs([get_icc_profile_size, _read_icc_profile])
def read_icc_profile(slide: _OpenSlide) -> bytes | None:
    size = get_icc_profile_size(slide)
    if size == 0:
        return None
    buf = (size * c_char)()
    _read_icc_profile(slide, buf)
    return buf.raw


get_error: _Func[[_OpenSlide], str] = _func(
    'openslide_get_error', c_char_p, [_OpenSlide], _check_string
)

get_property_names: _Func[[_OpenSlide], list[str]] = _func(
    'openslide_get_property_names', POINTER(c_char_p), [_OpenSlide], _check_name_list
)

get_property_value: _Func[[_OpenSlide, str | bytes], str] = _func(
    'openslide_get_property_value', c_char_p, [_OpenSlide, _utf8_p]
)

get_associated_image_names: _Func[[_OpenSlide], list[str]] = _func(
    'openslide_get_associated_image_names',
    POINTER(c_char_p),
    [_OpenSlide],
    _check_name_list,
)

_get_associated_image_dimensions: _Func[
    [_OpenSlide, str | bytes, _Pointer[c_int64], _Pointer[c_int64]], None
] = _func(
    'openslide_get_associated_image_dimensions',
    None,
    [_OpenSlide, _utf8_p, POINTER(c_int64), POINTER(c_int64)],
)


@_wraps_funcs([_get_associated_image_dimensions])
def get_associated_image_dimensions(
    slide: _OpenSlide, name: str | bytes
) -> tuple[int, int]:
    w, h = c_int64(), c_int64()
    _get_associated_image_dimensions(slide, name, byref(w), byref(h))
    return w.value, h.value


_read_associated_image: _Func[[_OpenSlide, str | bytes, _Pointer[c_uint32]], None] = (
    _func(
        'openslide_read_associated_image',
        None,
        [_OpenSlide, _utf8_p, POINTER(c_uint32)],
    )
)


@_wraps_funcs([get_associated_image_dimensions, _read_associated_image])
def read_associated_image(slide: _OpenSlide, name: str | bytes) -> Image.Image:
    w, h = get_associated_image_dimensions(slide, name)
    buf = (w * h * c_uint32)()
    _read_associated_image(slide, name, buf)
    return _load_image(buf, (w, h))


get_associated_image_icc_profile_size: _Func[[_OpenSlide, str | bytes], int] = _func(
    'openslide_get_associated_image_icc_profile_size',
    c_int64,
    [_OpenSlide, _utf8_p],
    minimum_version='4.0.0',
)

_read_associated_image_icc_profile: _Func[
    [_OpenSlide, str | bytes, _Pointer[c_char]], None
] = _func(
    'openslide_read_associated_image_icc_profile',
    None,
    [_OpenSlide, _utf8_p, POINTER(c_char)],
    minimum_version='4.0.0',
)


@_wraps_funcs(
    [get_associated_image_icc_profile_size, _read_associated_image_icc_profile]
)
def read_associated_image_icc_profile(
    slide: _OpenSlide, name: str | bytes
) -> bytes | None:
    size = get_associated_image_icc_profile_size(slide, name)
    if size == 0:
        return None
    buf = (size * c_char)()
    _read_associated_image_icc_profile(slide, name, buf)
    return buf.raw


get_version: _Func[[], str] = _func(
    'openslide_get_version', c_char_p, [], _check_string
)

cache_create: _Func[[int], _OpenSlideCache] = _func(
    'openslide_cache_create',
    c_void_p,
    [_size_t],
    _check_cache_create,
    minimum_version='4.0.0',
)

set_cache: _Func[[_OpenSlide, _OpenSlideCache], None] = _func(
    'openslide_set_cache',
    None,
    [_OpenSlide, _OpenSlideCache],
    minimum_version='4.0.0',
)

cache_release: _Func[[_OpenSlideCache], None] = _func(
    'openslide_cache_release', None, [_OpenSlideCache], None, minimum_version='4.0.0'
)
