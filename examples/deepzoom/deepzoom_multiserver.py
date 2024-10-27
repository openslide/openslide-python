#!/usr/bin/env python
#
# deepzoom_multiserver - Example web application for viewing multiple slides
#
# Copyright (c) 2010-2015 Carnegie Mellon University
# Copyright (c) 2021-2024 Benjamin Gilbert
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

from __future__ import annotations

from argparse import ArgumentParser
import base64
from collections import OrderedDict
from collections.abc import Callable
from io import BytesIO
import os
from pathlib import Path, PurePath
from threading import Lock
from typing import TYPE_CHECKING, Any, Literal
import zlib

from PIL import Image, ImageCms
from flask import Flask, Response, abort, make_response, render_template, url_for

if TYPE_CHECKING:
    # Python 3.10+
    from typing import TypeAlias

if os.name == 'nt':
    _dll_path = os.getenv('OPENSLIDE_PATH')
    if _dll_path is not None:
        with os.add_dll_directory(_dll_path):  # type: ignore[attr-defined,unused-ignore]  # noqa: E501
            import openslide
    else:
        import openslide
else:
    import openslide

from openslide import OpenSlide, OpenSlideCache, OpenSlideError, OpenSlideVersionError
from openslide.deepzoom import DeepZoomGenerator

# Optimized sRGB v2 profile, CC0-1.0 license
# https://github.com/saucecontrol/Compact-ICC-Profiles/blob/bdd84663/profiles/sRGB-v2-micro.icc
# ImageCms.createProfile() generates a v4 profile and Firefox has problems
# with those: https://littlecms.com/blog/2020/09/09/browser-check/
SRGB_PROFILE_BYTES = zlib.decompress(
    base64.b64decode(
        'eNpjYGA8kZOcW8wkwMCQm1dSFOTupBARGaXA/oiBmUGEgZOBj0E2Mbm4wDfYLYQBCIoT'
        'y4uTS4pyGFDAt2sMjCD6sm5GYl7K3IkMtg4NG2wdSnQa5y1V6mPADzhTUouTgfQHII5P'
        'LigqYWBg5AGyecpLCkBsCSBbpAjoKCBbB8ROh7AdQOwkCDsErCYkyBnIzgCyE9KR2ElI'
        'bKhdIMBaCvQsskNKUitKQLSzswEDKAwgop9DwH5jFDuJEMtfwMBg8YmBgbkfIZY0jYFh'
        'eycDg8QthJgKUB1/KwPDtiPJpUVlUGu0gLiG4QfjHKZS5maWk2x+HEJcEjxJfF8Ez4t8'
        'k8iS0VNwVlmjmaVXZ/zacrP9NbdwX7OQshjxFNmcttKwut4OnUlmc1Yv79l0e9/MU8ev'
        'pz4p//jz/38AR4Nk5Q=='
    )
)
SRGB_PROFILE = ImageCms.getOpenProfile(BytesIO(SRGB_PROFILE_BYTES))

if TYPE_CHECKING:
    ColorMode: TypeAlias = Literal[
        'default',
        'absolute-colorimetric',
        'perceptual',
        'relative-colorimetric',
        'saturation',
        'embed',
        'ignore',
    ]
    Transform: TypeAlias = Callable[[Image.Image], None]


class DeepZoomMultiServer(Flask):
    basedir: Path
    cache: _SlideCache


class AnnotatedDeepZoomGenerator(DeepZoomGenerator):
    filename: str
    mpp: float
    transform: Transform


def create_app(
    config: dict[str, Any] | None = None,
    config_file: Path | None = None,
) -> Flask:
    # Create and configure app
    app = DeepZoomMultiServer(__name__)
    app.config.from_mapping(
        SLIDE_DIR='.',
        SLIDE_CACHE_SIZE=10,
        SLIDE_TILE_CACHE_MB=128,
        DEEPZOOM_FORMAT='jpeg',
        DEEPZOOM_TILE_SIZE=254,
        DEEPZOOM_OVERLAP=1,
        DEEPZOOM_LIMIT_BOUNDS=True,
        DEEPZOOM_TILE_QUALITY=75,
        DEEPZOOM_COLOR_MODE='default',
    )
    app.config.from_envvar('DEEPZOOM_MULTISERVER_SETTINGS', silent=True)
    if config_file is not None:
        app.config.from_pyfile(config_file)
    if config is not None:
        app.config.from_mapping(config)

    # Set up cache
    app.basedir = Path(app.config['SLIDE_DIR']).resolve(strict=True)
    config_map = {
        'DEEPZOOM_TILE_SIZE': 'tile_size',
        'DEEPZOOM_OVERLAP': 'overlap',
        'DEEPZOOM_LIMIT_BOUNDS': 'limit_bounds',
    }
    opts = {v: app.config[k] for k, v in config_map.items()}
    app.cache = _SlideCache(
        app.config['SLIDE_CACHE_SIZE'],
        app.config['SLIDE_TILE_CACHE_MB'],
        opts,
        app.config['DEEPZOOM_COLOR_MODE'],
    )

    # Helper functions
    def get_slide(user_path: PurePath) -> AnnotatedDeepZoomGenerator:
        try:
            path = (app.basedir / user_path).resolve(strict=True)
        except OSError:
            # Does not exist
            abort(404)
        if path.parts[: len(app.basedir.parts)] != app.basedir.parts:
            # Directory traversal
            abort(404)
        try:
            slide = app.cache.get(path)
            slide.filename = path.name
            return slide
        except OpenSlideError:
            abort(404)

    # Set up routes
    @app.route('/')
    def index() -> str:
        return render_template('files.html', root_dir=_Directory(app.basedir))

    @app.route('/<path:path>')
    def slide(path: str) -> str:
        slide = get_slide(PurePath(path))
        slide_url = url_for('dzi', path=path)
        return render_template(
            'slide-fullpage.html',
            slide_url=slide_url,
            slide_filename=slide.filename,
            slide_mpp=slide.mpp,
        )

    @app.route('/<path:path>.dzi')
    def dzi(path: str) -> Response:
        slide = get_slide(PurePath(path))
        format = app.config['DEEPZOOM_FORMAT']
        resp = make_response(slide.get_dzi(format))
        resp.mimetype = 'application/xml'
        return resp

    @app.route('/<path:path>_files/<int:level>/<int:col>_<int:row>.<format>')
    def tile(path: str, level: int, col: int, row: int, format: str) -> Response:
        slide = get_slide(PurePath(path))
        format = format.lower()
        if format != 'jpeg' and format != 'png':
            # Not supported by Deep Zoom
            abort(404)
        try:
            tile = slide.get_tile(level, (col, row))
        except ValueError:
            # Invalid level or coordinates
            abort(404)
        slide.transform(tile)
        buf = BytesIO()
        tile.save(
            buf,
            format,
            quality=app.config['DEEPZOOM_TILE_QUALITY'],
            icc_profile=tile.info.get('icc_profile'),
        )
        resp = make_response(buf.getvalue())
        resp.mimetype = 'image/%s' % format
        return resp

    return app


class _SlideCache:
    def __init__(
        self,
        cache_size: int,
        tile_cache_mb: int,
        dz_opts: dict[str, Any],
        color_mode: ColorMode,
    ):
        self.cache_size = cache_size
        self.dz_opts = dz_opts
        self.color_mode = color_mode
        self._lock = Lock()
        self._cache: OrderedDict[Path, AnnotatedDeepZoomGenerator] = OrderedDict()
        # Share a single tile cache among all slide handles, if supported
        try:
            self._tile_cache: OpenSlideCache | None = OpenSlideCache(
                tile_cache_mb * 1024 * 1024
            )
        except OpenSlideVersionError:
            self._tile_cache = None

    def get(self, path: Path) -> AnnotatedDeepZoomGenerator:
        with self._lock:
            if path in self._cache:
                # Move to end of LRU
                slide = self._cache.pop(path)
                self._cache[path] = slide
                return slide

        osr = OpenSlide(path)
        if self._tile_cache is not None:
            osr.set_cache(self._tile_cache)
        slide = AnnotatedDeepZoomGenerator(osr, **self.dz_opts)
        try:
            mpp_x = osr.properties[openslide.PROPERTY_NAME_MPP_X]
            mpp_y = osr.properties[openslide.PROPERTY_NAME_MPP_Y]
            slide.mpp = (float(mpp_x) + float(mpp_y)) / 2
        except (KeyError, ValueError):
            slide.mpp = 0
        slide.transform = self._get_transform(osr)

        with self._lock:
            if path not in self._cache:
                if len(self._cache) == self.cache_size:
                    self._cache.popitem(last=False)
                self._cache[path] = slide
        return slide

    def _get_transform(self, image: OpenSlide) -> Transform:
        if image.color_profile is None:
            return lambda img: None
        mode = self.color_mode
        if mode == 'ignore':
            # drop ICC profile from tiles
            return lambda img: img.info.pop('icc_profile')
        elif mode == 'embed':
            # embed ICC profile in tiles
            return lambda img: None
        elif mode == 'default':
            intent = ImageCms.Intent(ImageCms.getDefaultIntent(image.color_profile))
        elif mode == 'absolute-colorimetric':
            intent = ImageCms.Intent.ABSOLUTE_COLORIMETRIC
        elif mode == 'relative-colorimetric':
            intent = ImageCms.Intent.RELATIVE_COLORIMETRIC
        elif mode == 'perceptual':
            intent = ImageCms.Intent.PERCEPTUAL
        elif mode == 'saturation':
            intent = ImageCms.Intent.SATURATION
        else:
            raise ValueError(f'Unknown color mode {mode}')
        transform = ImageCms.buildTransform(
            image.color_profile,
            SRGB_PROFILE,
            'RGB',
            'RGB',
            intent,
            ImageCms.Flags(0),
        )

        def xfrm(img: Image.Image) -> None:
            ImageCms.applyTransform(img, transform, True)
            # Some browsers assume we intend the display's color space if we
            # don't embed the profile.  Pillow's serialization is larger, so
            # use ours.
            img.info['icc_profile'] = SRGB_PROFILE_BYTES

        return xfrm


class _Directory:
    _DEFAULT_RELPATH = PurePath('.')

    def __init__(self, basedir: Path, relpath: PurePath = _DEFAULT_RELPATH):
        self.name = relpath.name
        self.children: list[_Directory | _SlideFile] = []
        for cur_path in sorted((basedir / relpath).iterdir()):
            cur_relpath = relpath / cur_path.name
            if cur_path.is_dir():
                cur_dir = _Directory(basedir, cur_relpath)
                if cur_dir.children:
                    self.children.append(cur_dir)
            elif OpenSlide.detect_format(cur_path):
                self.children.append(_SlideFile(cur_relpath))


class _SlideFile:
    def __init__(self, relpath: PurePath):
        self.name = relpath.name
        self.url_path = relpath.as_posix()


if __name__ == '__main__':
    parser = ArgumentParser(usage='%(prog)s [options] [SLIDE-DIRECTORY]')
    parser.add_argument(
        '-B',
        '--ignore-bounds',
        dest='DEEPZOOM_LIMIT_BOUNDS',
        default=True,
        action='store_false',
        help='display entire scan area',
    )
    parser.add_argument(
        '--color-mode',
        dest='DEEPZOOM_COLOR_MODE',
        choices=[
            'default',
            'absolute-colorimetric',
            'perceptual',
            'relative-colorimetric',
            'saturation',
            'embed',
            'ignore',
        ],
        default='default',
        help=(
            'convert tiles to sRGB using default rendering intent of ICC '
            'profile, or specified rendering intent; or embed original '
            'ICC profile; or ignore ICC profile (compat) [default]'
        ),
    )
    parser.add_argument(
        '-c', '--config', metavar='FILE', type=Path, dest='config', help='config file'
    )
    parser.add_argument(
        '-d',
        '--debug',
        dest='DEBUG',
        action='store_true',
        help='run in debugging mode (insecure)',
    )
    parser.add_argument(
        '-e',
        '--overlap',
        metavar='PIXELS',
        dest='DEEPZOOM_OVERLAP',
        type=int,
        help='overlap of adjacent tiles [1]',
    )
    parser.add_argument(
        '-f',
        '--format',
        dest='DEEPZOOM_FORMAT',
        choices=['jpeg', 'png'],
        help='image format for tiles [jpeg]',
    )
    parser.add_argument(
        '-l',
        '--listen',
        metavar='ADDRESS',
        dest='host',
        default='127.0.0.1',
        help='address to listen on [127.0.0.1]',
    )
    parser.add_argument(
        '-p',
        '--port',
        metavar='PORT',
        dest='port',
        type=int,
        default=5000,
        help='port to listen on [5000]',
    )
    parser.add_argument(
        '-Q',
        '--quality',
        metavar='QUALITY',
        dest='DEEPZOOM_TILE_QUALITY',
        type=int,
        help='JPEG compression quality [75]',
    )
    parser.add_argument(
        '-s',
        '--size',
        metavar='PIXELS',
        dest='DEEPZOOM_TILE_SIZE',
        type=int,
        help='tile size [254]',
    )
    parser.add_argument(
        'SLIDE_DIR',
        metavar='SLIDE-DIRECTORY',
        type=Path,
        nargs='?',
        help='slide directory',
    )

    args = parser.parse_args()
    config = {}
    config_file = args.config
    # Set only those settings specified on the command line
    for k in dir(args):
        v = getattr(args, k)
        if not k.startswith('_') and v is not None:
            config[k] = v
    app = create_app(config, config_file)

    app.run(host=args.host, port=args.port, threaded=True)
