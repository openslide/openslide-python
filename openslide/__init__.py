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

"""A library for reading whole-slide images.

This package provides Python bindings for the OpenSlide library.  For
documentation on the OpenSlide API, see:

http://openslide.org/api/openslide_8h.html
"""

from collections import Mapping

from openslide import lowlevel

# For the benefit of library users
from openslide.lowlevel import OpenSlideError
from openslide._version import __version__

PROPERTY_NAME_COMMENT          = 'openslide.comment'
PROPERTY_NAME_VENDOR           = 'openslide.vendor'
PROPERTY_NAME_QUICKHASH1       = 'openslide.quickhash-1'
PROPERTY_NAME_BACKGROUND_COLOR = 'openslide.background-color'

class OpenSlide(object):
    """An open whole-slide image.

    close() is called automatically when the object is deleted.  In
    addition, an OpenSlide object may be used as a context manager, and
    will be closed when exiting the context.

    If an operation fails, OpenSlideError is raised.  Note that OpenSlide
    has latching error semantics: once OpenSlideError is raised, all future
    operations on the OpenSlide object, other than close(), will fail.
    """

    def __init__(self, filename):
        """Open a whole-slide image."""
        self._osr = lowlevel.open(filename)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __del__(self):
        if getattr(self, '_osr', None) is not None:
            self.close()

    @classmethod
    def can_open(cls, filename):
        """Return True if OpenSlide can read the specified file."""
        return lowlevel.can_open(filename)

    def close(self):
        """Close the OpenSlide object."""
        lowlevel.close(self._osr)
        self._osr = None

    @property
    def layer_count(self):
        """The number of layers in the image."""
        return lowlevel.get_layer_count(self._osr)

    @property
    def layer_dimensions(self):
        """A list of (width, height) tuples, one for each layer of the image.

        layer_dimensions[n] contains the dimensions of layer n."""
        return tuple(lowlevel.get_layer_dimensions(self._osr, i)
                for i in range(self.layer_count))

    @property
    def dimensions(self):
        """A (width, height) tuple for layer 0 of the image."""
        return self.layer_dimensions[0]

    @property
    def layer_downsamples(self):
        """A list of downsampling factors for each layer of the image.

        layer_downsample[n] contains the downsample factor of layer n."""
        return tuple(lowlevel.get_layer_downsample(self._osr, i)
                for i in range(self.layer_count))

    @property
    def properties(self):
        """Metadata about the image.

        This is a map: property name -> property value."""
        return _PropertyMap(self._osr)

    @property
    def associated_images(self):
        """Images associated with this whole-slide image.

        This is a map: image name -> PIL.Image.

        Unlike in the C interface, the images accessible via this property
        are not premultiplied."""
        return _AssociatedImageMap(self._osr)

    def get_best_layer_for_downsample(self, downsample):
        """Return the best layer for displaying the given downsample."""
        return lowlevel.get_best_layer_for_downsample(self._osr, downsample)

    def read_region(self, location, layer, size):
        """Return a PIL.Image containing the contents of the region.

        location: (x, y) tuple giving the top left pixel in the layer 0
                  reference frame.
        layer:    the layer number.
        size:     (width, height) tuple giving the region size.

        Unlike in the C interface, the image data returned by this
        function is not premultiplied."""
        return lowlevel.read_region(self._osr, location[0], location[1],
                layer, size[0], size[1])


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
        return lowlevel.get_property_names(self._osr)

    def __getitem__(self, key):
        v = lowlevel.get_property_value(self._osr, key)
        if v is None:
            raise KeyError()
        return v


class _AssociatedImageMap(_OpenSlideMap):
    def keys(self):
        return lowlevel.get_associated_image_names(self._osr)

    def __getitem__(self, key):
        if key not in self.keys():
            raise KeyError()
        return lowlevel.read_associated_image(self._osr, key)


if __name__ == '__main__':
    import sys
    print "Can open:", OpenSlide.can_open(sys.argv[1])
    with OpenSlide(sys.argv[1]) as _slide:
        print "Dimensions:", _slide.dimensions
        print "Layers:", _slide.layer_count
        print "Layer dimensions:", _slide.layer_dimensions
        print "Layer downsamples:", _slide.layer_downsamples
        print "Properties:", _slide.properties
        print "Associated images:", _slide.associated_images
