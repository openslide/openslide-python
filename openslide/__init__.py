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

from collections import Mapping

import openslide.lowlevel as _ll

# For the benefit of library users
from openslide.lowlevel import OpenSlideError
from openslide._version import __version__

PROPERTY_NAME_COMMENT          = 'openslide.comment'
PROPERTY_NAME_VENDOR           = 'openslide.vendor'
PROPERTY_NAME_QUICKHASH1       = 'openslide.quickhash-1'
PROPERTY_NAME_BACKGROUND_COLOR = 'openslide.background-color'

class OpenSlide(object):
    def __init__(self, filename):
        self._osr = _ll.open(filename)
        self.properties = _PropertyMap(self._osr)
        self.associated_images = _AssociatedImageMap(self._osr)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __del__(self):
        if getattr(self, '_osr', None) is not None:
            self.close()

    @classmethod
    def can_open(self, filename):
        return _ll.can_open(filename)

    def close(self):
        _ll.close(self._osr)
        self._osr = None

    @property
    def layer_count(self):
        return _ll.get_layer_count(self._osr)

    @property
    def layer_dimensions(self):
        return tuple(_ll.get_layer_dimensions(self._osr, i)
                for i in range(self.layer_count))

    @property
    def dimensions(self):
        return self.layer_dimensions[0]

    @property
    def layer_downsample(self):
        return tuple(_ll.get_layer_downsample(self._osr, i)
                for i in range(self.layer_count))

    def get_best_layer_for_downsample(self, downsample):
        return _ll.get_best_layer_for_downsample(self._osr, downsample)

    def read_region(self, x, y, layer, w, h):
        return _ll.read_region(self._osr, x, y, layer, w, h)


class _OpenSlideMap(Mapping):
    def __init__(self, osr):
        self._osr = osr

    def __repr__(self):
        return repr(dict(self))

    def __len__(self):
        return len(self.keys())

    def __iter__(self):
        return iter(self.keys())

    def keys(self):
        raise NotImplementedError()


class _PropertyMap(_OpenSlideMap):
    def keys(self):
        return _ll.get_property_names(self._osr)

    def __getitem__(self, key):
        v = _ll.get_property_value(self._osr, key)
        if v is None:
            raise KeyError()
        return v


class _AssociatedImageMap(_OpenSlideMap):
    def keys(self):
        return _ll.get_associated_image_names(self._osr)

    def __getitem__(self, key):
        if key not in self.keys():
            raise KeyError()
        return _ll.read_associated_image(self._osr, key)


if __name__ == '__main__':
    import sys
    print "Can open:", OpenSlide.can_open(sys.argv[1])
    with OpenSlide(sys.argv[1]) as _slide:
        print "Dimensions:", _slide.dimensions
        print "Layers:", _slide.layer_count
        print "Layer dimensions:", _slide.layer_dimensions
        print "Layer downsamples:", _slide.layer_downsample
        print "Properties:", _slide.properties
        print "Associated images:", _slide.associated_images
