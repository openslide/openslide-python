#!/usr/bin/env python
#
# deepzoom_server - Example web application for serving whole-slide images
#
# Copyright (c) 2010-2015 Carnegie Mellon University
# Copyright (c) 2023      Benjamin Gilbert
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

from argparse import ArgumentParser
import base64
from io import BytesIO
import os
import re
from unicodedata import normalize
import zlib

from PIL import ImageCms
from flask import Flask, abort, make_response, render_template, url_for

if os.name == 'nt':
    _dll_path = os.getenv('OPENSLIDE_PATH')
    if _dll_path is not None:
        with os.add_dll_directory(_dll_path):
            import openslide
    else:
        import openslide
else:
    import openslide

from openslide import ImageSlide, open_slide
from openslide.deepzoom import DeepZoomGenerator

SLIDE_NAME = 'slide'

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


def create_app(config=None, config_file=None):
    # Create and configure app
    app = Flask(__name__)
    app.config.from_mapping(
        DEEPZOOM_SLIDE=None,
        DEEPZOOM_FORMAT='jpeg',
        DEEPZOOM_TILE_SIZE=254,
        DEEPZOOM_OVERLAP=1,
        DEEPZOOM_LIMIT_BOUNDS=True,
        DEEPZOOM_TILE_QUALITY=75,
        DEEPZOOM_COLOR_MODE='absolute-colorimetric',
    )
    app.config.from_envvar('DEEPZOOM_TILER_SETTINGS', silent=True)
    if config_file is not None:
        app.config.from_pyfile(config_file)
    if config is not None:
        app.config.from_mapping(config)

    # Open slide
    slidefile = app.config['DEEPZOOM_SLIDE']
    if slidefile is None:
        raise ValueError('No slide file specified')
    config_map = {
        'DEEPZOOM_TILE_SIZE': 'tile_size',
        'DEEPZOOM_OVERLAP': 'overlap',
        'DEEPZOOM_LIMIT_BOUNDS': 'limit_bounds',
    }
    opts = {v: app.config[k] for k, v in config_map.items()}
    slide = open_slide(slidefile)
    app.slides = {SLIDE_NAME: DeepZoomGenerator(slide, **opts)}
    app.transforms = {
        SLIDE_NAME: get_transform(slide, app.config['DEEPZOOM_COLOR_MODE'])
    }
    app.associated_images = []
    app.slide_properties = slide.properties
    for name, image in slide.associated_images.items():
        app.associated_images.append(name)
        slug = slugify(name)
        image_slide = ImageSlide(image)
        app.slides[slug] = DeepZoomGenerator(image_slide, **opts)
        app.transforms[slug] = get_transform(
            image_slide, app.config['DEEPZOOM_COLOR_MODE']
        )
    try:
        mpp_x = slide.properties[openslide.PROPERTY_NAME_MPP_X]
        mpp_y = slide.properties[openslide.PROPERTY_NAME_MPP_Y]
        app.slide_mpp = (float(mpp_x) + float(mpp_y)) / 2
    except (KeyError, ValueError):
        app.slide_mpp = 0

    # Set up routes
    @app.route('/')
    def index():
        slide_url = url_for('dzi', slug=SLIDE_NAME)
        associated_urls = {
            name: url_for('dzi', slug=slugify(name)) for name in app.associated_images
        }
        return render_template(
            'slide-multipane.html',
            slide_url=slide_url,
            associated=associated_urls,
            properties=app.slide_properties,
            slide_mpp=app.slide_mpp,
        )

    @app.route('/<slug>.dzi')
    def dzi(slug):
        format = app.config['DEEPZOOM_FORMAT']
        try:
            resp = make_response(app.slides[slug].get_dzi(format))
            resp.mimetype = 'application/xml'
            return resp
        except KeyError:
            # Unknown slug
            abort(404)

    @app.route('/<slug>_files/<int:level>/<int:col>_<int:row>.<format>')
    def tile(slug, level, col, row, format):
        format = format.lower()
        if format != 'jpeg' and format != 'png':
            # Not supported by Deep Zoom
            abort(404)
        try:
            tile = app.slides[slug].get_tile(level, (col, row))
        except KeyError:
            # Unknown slug
            abort(404)
        except ValueError:
            # Invalid level or coordinates
            abort(404)
        app.transforms[slug](tile)
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


def slugify(text):
    text = normalize('NFKD', text.lower()).encode('ascii', 'ignore').decode()
    return re.sub('[^a-z0-9]+', '-', text)


def get_transform(image, mode):
    if image.color_profile is None:
        return lambda img: None
    if mode == 'ignore':
        # drop ICC profile from tiles
        return lambda img: img.info.pop('icc_profile')
    elif mode == 'embed':
        # embed ICC profile in tiles
        return lambda img: None
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
        0,
    )

    def xfrm(img):
        ImageCms.applyTransform(img, transform, True)
        # Some browsers assume we intend the display's color space if we don't
        # embed the profile.  Pillow's serialization is larger, so use ours.
        img.info['icc_profile'] = SRGB_PROFILE_BYTES

    return xfrm


if __name__ == '__main__':
    parser = ArgumentParser(usage='%(prog)s [options] [SLIDE]')
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
            'absolute-colorimetric',
            'perceptual',
            'relative-colorimetric',
            'saturation',
            'embed',
            'ignore',
        ],
        default='absolute-colorimetric',
        help=(
            'convert tiles to sRGB using specified rendering intent, or '
            'embed original ICC profile, or ignore ICC profile (compat) '
            '[absolute-colorimetric]'
        ),
    )
    parser.add_argument(
        '-c', '--config', metavar='FILE', dest='config', help='config file'
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
        metavar='{jpeg|png}',
        dest='DEEPZOOM_FORMAT',
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
        'DEEPZOOM_SLIDE',
        metavar='SLIDE',
        nargs='?',
        help='slide file',
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
