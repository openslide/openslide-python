#!/usr/bin/env python
#
# deepzoom_server - Example web application for serving whole-slide images
#
# Copyright (c) 2010-2015 Carnegie Mellon University
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

from io import BytesIO
from optparse import OptionParser
import os
import re
from unicodedata import normalize
from functools import lru_cache

import PIL
from PIL import ImageFile, ImageCms, Image

from flask import Flask, abort, make_response, render_template, url_for

if os.name == 'nt':
    _dll_path = os.getenv('OPENSLIDE_PATH')
    if _dll_path is not None:
        if hasattr(os, 'add_dll_directory'):
            # Python >= 3.8
            with os.add_dll_directory(_dll_path):
                import openslide
        else:
            # Python < 3.8
            _orig_path = os.environ.get('PATH', '')
            os.environ['PATH'] = _orig_path + ';' + _dll_path
            import openslide

            os.environ['PATH'] = _orig_path
else:
    import openslide

from openslide import ImageSlide, open_slide
from openslide.deepzoom import DeepZoomGenerator

SLIDE_NAME = 'slide'


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
    app.associated_images = []
    app.slide_properties = slide.properties
    for name, image in slide.associated_images.items():
        app.associated_images.append(name)
        slug = slugify(name)
        app.slides[slug] = DeepZoomGenerator(ImageSlide(image), **opts)
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
            if app.config["USE_ICC"]:
                tile = icc_apply(img=tile, fname=config['DEEPZOOM_SLIDE'])
        except KeyError:
            # Unknown slug
            abort(404)
        except ValueError:
            # Invalid level or coordinates
            abort(404)
        buf = BytesIO()
        tile.save(buf, format, quality=app.config['DEEPZOOM_TILE_QUALITY'])
        resp = make_response(buf.getvalue())
        resp.mimetype = 'image/%s' % format
        return resp

    return app


def slugify(text):
    text = normalize('NFKD', text.lower()).encode('ascii', 'ignore').decode()
    return re.sub('[^a-z0-9]+', '-', text)

def icc_apply(img, fname):
    icc_profile = get_icc_profile(fname)
    if icc_profile is None:
        return img
    else:
        return ImageCms.applyTransform(img, icc_profile)
    
    
@lru_cache()
def get_icc_profile(fname):
    #Source: http://www.andrewjanowczyk.com/application-of-icc-profiles-to-digital-pathology-images/
    
    if fname is None:
        fname = app.config['DEEPZOOM_SLIDE']

    ImageFile.LOAD_TRUNCATED_IMAGES = True
 
    #Need to set this to none, otherwise PIL raises an error as its concerned our image is too big and is in fact a decompression bomb
    Image.MAX_IMAGE_PIXELS = None

    try:
        icc = Image.open(fname).info.get('icc_profile') 
    except PIL.UnidentifiedImageError:
        return
    
    if icc is not None:
        f = BytesIO(icc)
        prf = ImageCms.ImageCmsProfile(f)

        #create a profile for RGB 
        rgbp=ImageCms.createProfile("sRGB")
        #and build a transform to for our RGB to ICC space, so that we can apply it faster later
        #Update Nov2022, it was pointed out to me that the previous version of this code had the two profiles switched
        #however when I tested both versions, the 'swapped' version appeared to result in a better colored image
        #practically speaking, I'm unsure what to make of that...i leave it to the user to decide is it better for it to be correct or for it to look nicer?
        #experiments to be done....

        #icc2rgb = ImageCms.buildTransformFromOpenProfiles(rgbp, prf, "RGB", "RGB") #inverted version
        icc2rgb = ImageCms.buildTransformFromOpenProfiles(prf,rgbp, "RGB", "RGB")   #correct version

        return icc2rgb
    else:
        return


if __name__ == '__main__':
    parser = OptionParser(usage='Usage: %prog [options] [slide]')
    parser.add_option(
        '-B',
        '--ignore-bounds',
        dest='DEEPZOOM_LIMIT_BOUNDS',
        default=True,
        action='store_false',
        help='display entire scan area',
    )
    parser.add_option(
        '-c', '--config', metavar='FILE', dest='config', help='config file'
    )
    parser.add_option(
        '-d',
        '--debug',
        dest='DEBUG',
        action='store_true',
        help='run in debugging mode (insecure)',
    )
    parser.add_option(
        '-e',
        '--overlap',
        metavar='PIXELS',
        dest='DEEPZOOM_OVERLAP',
        type='int',
        help='overlap of adjacent tiles [1]',
    )
    parser.add_option(
        '-f',
        '--format',
        metavar='{jpeg|png}',
        dest='DEEPZOOM_FORMAT',
        help='image format for tiles [jpeg]',
    )
    parser.add_option(
        '-l',
        '--listen',
        metavar='ADDRESS',
        dest='host',
        default='127.0.0.1',
        help='address to listen on [127.0.0.1]',
    )
    parser.add_option(
        '-p',
        '--port',
        metavar='PORT',
        dest='port',
        type='int',
        default=5000,
        help='port to listen on [5000]',
    )
    parser.add_option(
        '-Q',
        '--quality',
        metavar='QUALITY',
        dest='DEEPZOOM_TILE_QUALITY',
        type='int',
        help='JPEG compression quality [75]',
    )
    parser.add_option(
        '-s',
        '--size',
        metavar='PIXELS',
        dest='DEEPZOOM_TILE_SIZE',
        type='int',
        help='tile size [254]',
    )

    parser.add_option(
        '-i',
        '--apply-icc',
        default=False,
        action="store_true",
        dest="USE_ICC",
        help='apply icc if file has icc profile',
    )

    (opts, args) = parser.parse_args()
    config = {}
    config_file = opts.config
    # Set only those settings specified on the command line
    for k in dir(opts):
        v = getattr(opts, k)
        if not k.startswith('_') and v is not None:
            config[k] = v
    # Set slide file if specified
    try:
        config['DEEPZOOM_SLIDE'] = args[0]
    except IndexError:
        pass
    app = create_app(config, config_file)

    app.run(host=opts.host, port=opts.port, threaded=True)
