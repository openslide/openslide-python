#
# openslide-python - Python bindings for the OpenSlide library
#
# Copyright (c) 2010-2014 Carnegie Mellon University
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

This package provides Python bindings for the OpenSlide library.
"""

from __future__ import division, print_function
from collections import Mapping
from PIL import Image

from openslide import lowlevel

# For the benefit of library users
from openslide.lowlevel import OpenSlideError, OpenSlideUnsupportedFormatError
from openslide._version import __version__

__library_version__ = lowlevel.get_version()

PROPERTY_NAME_COMMENT          = u'openslide.comment'
PROPERTY_NAME_VENDOR           = u'openslide.vendor'
PROPERTY_NAME_QUICKHASH1       = u'openslide.quickhash-1'
PROPERTY_NAME_BACKGROUND_COLOR = u'openslide.background-color'
PROPERTY_NAME_OBJECTIVE_POWER  = u'openslide.objective-power'
PROPERTY_NAME_MPP_X            = u'openslide.mpp-x'
PROPERTY_NAME_MPP_Y            = u'openslide.mpp-y'
PROPERTY_NAME_BOUNDS_X         = u'openslide.bounds-x'
PROPERTY_NAME_BOUNDS_Y         = u'openslide.bounds-y'
PROPERTY_NAME_BOUNDS_WIDTH     = u'openslide.bounds-width'
PROPERTY_NAME_BOUNDS_HEIGHT    = u'openslide.bounds-height'

class AbstractSlide(object):
    """The base class of a slide object."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    @classmethod
    def detect_format(cls, filename):
        """Return a string describing the format of the specified file.

        If the file format is not recognized, return None."""
        raise NotImplementedError

    def close(self):
        """Close the slide."""
        raise NotImplementedError

    @property
    def level_count(self):
        """The number of levels in the image."""
        raise NotImplementedError

    @property
    def level_dimensions(self):
        """A list of (width, height) tuples, one for each level of the image.

        level_dimensions[n] contains the dimensions of level n."""
        raise NotImplementedError

    @property
    def dimensions(self):
        """A (width, height) tuple for level 0 of the image."""
        return self.level_dimensions[0]

    @property
    def level_downsamples(self):
        """A list of downsampling factors for each level of the image.

        level_downsample[n] contains the downsample factor of level n."""
        raise NotImplementedError

    @property
    def properties(self):
        """Metadata about the image.

        This is a map: property name -> property value."""
        raise NotImplementedError

    @property
    def associated_images(self):
        """Images associated with this whole-slide image.

        This is a map: image name -> PIL.Image."""
        raise NotImplementedError

    def get_best_level_for_downsample(self, downsample):
        """Return the best level for displaying the given downsample."""
        raise NotImplementedError

    def read_region(self, location, level, size):
        """Return a PIL.Image containing the contents of the region.

        location: (x, y) tuple giving the top left pixel in the level 0
                  reference frame.
        level:    the level number.
        size:     (width, height) tuple giving the region size."""
        raise NotImplementedError

    def get_thumbnail(self, size):
        """Return a PIL.Image containing an RGB thumbnail of the image.

        size:     the maximum size of the thumbnail."""
        downsample = max(*[dim / thumb for dim, thumb in
                zip(self.dimensions, size)])
        level = self.get_best_level_for_downsample(downsample)
        tile = self.read_region((0, 0), level, self.level_dimensions[level])
        # Apply on solid background
        bg_color = '#' + self.properties.get(PROPERTY_NAME_BACKGROUND_COLOR,
                'ffffff')
        thumb = Image.new('RGB', tile.size, bg_color)
        thumb.paste(tile, None, tile)
        thumb.thumbnail(size, Image.ANTIALIAS)
        return thumb


class OpenSlide(AbstractSlide):
    """An open whole-slide image.

    close() is called automatically when the object is deleted.
    The object may be used as a context manager, in which case it will be
    closed upon exiting the context.

    If an operation fails, OpenSlideError is raised.  Note that OpenSlide
    has latching error semantics: once OpenSlideError is raised, all future
    operations on the OpenSlide object, other than close(), will fail.
    """

    def __init__(self, filename):
        """Open a whole-slide image."""
        AbstractSlide.__init__(self)
        self._filename = filename
        self._osr = lowlevel.open(filename)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._filename)

    @classmethod
    def detect_format(cls, filename):
        """Return a string describing the format vendor of the specified file.

        If the file format is not recognized, return None."""
        return lowlevel.detect_vendor(filename)

    def close(self):
        """Close the OpenSlide object."""
        lowlevel.close(self._osr)

    @property
    def level_count(self):
        """The number of levels in the image."""
        return lowlevel.get_level_count(self._osr)

    @property
    def level_dimensions(self):
        """A list of (width, height) tuples, one for each level of the image.

        level_dimensions[n] contains the dimensions of level n."""
        return tuple(lowlevel.get_level_dimensions(self._osr, i)
                for i in range(self.level_count))

    @property
    def level_downsamples(self):
        """A list of downsampling factors for each level of the image.

        level_downsample[n] contains the downsample factor of level n."""
        return tuple(lowlevel.get_level_downsample(self._osr, i)
                for i in range(self.level_count))

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

    def get_best_level_for_downsample(self, downsample):
        """Return the best level for displaying the given downsample."""
        return lowlevel.get_best_level_for_downsample(self._osr, downsample)

    def read_region(self, location, level, size):
        """Return a PIL.Image containing the contents of the region.

        location: (x, y) tuple giving the top left pixel in the level 0
                  reference frame.
        level:    the level number.
        size:     (width, height) tuple giving the region size.

        Unlike in the C interface, the image data returned by this
        function is not premultiplied."""
        return lowlevel.read_region(self._osr, location[0], location[1],
                level, size[0], size[1])


class _OpenSlideMap(Mapping):
    def __init__(self, osr):
        self._osr = osr

    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, dict(self))

    def __len__(self):
        return len(self._keys())

    def __iter__(self):
        return iter(self._keys())

    def _keys(self):
        # Private method; always returns list.
        raise NotImplementedError()


class _PropertyMap(_OpenSlideMap):
    def _keys(self):
        return lowlevel.get_property_names(self._osr)

    def __getitem__(self, key):
        v = lowlevel.get_property_value(self._osr, key)
        if v is None:
            raise KeyError()
        return v


class _AssociatedImageMap(_OpenSlideMap):
    def _keys(self):
        return lowlevel.get_associated_image_names(self._osr)

    def __getitem__(self, key):
        if key not in self._keys():
            raise KeyError()
        return lowlevel.read_associated_image(self._osr, key)


class ImageSlide(AbstractSlide):
    """A wrapper for a PIL.Image that provides the OpenSlide interface."""

    def __init__(self, file):
        """Open an image file.

        file can be a filename or a PIL.Image."""
        AbstractSlide.__init__(self)
        self._file_arg = file
        if isinstance(file, Image.Image):
            self._close = False
            self._image = file
        else:
            self._close = True
            self._image = Image.open(file)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._file_arg)

    @classmethod
    def detect_format(cls, filename):
        """Return a string describing the format of the specified file.

        If the file format is not recognized, return None."""
        try:
            img = Image.open(filename)
            format = img.format
            if hasattr(img, 'close'):
                # Pillow >= 2.5.0
                img.close()
            return format
        except IOError:
            return None

    def close(self):
        """Close the slide object."""
        if self._close:
            if hasattr(self._image, 'close'):
                # Pillow >= 2.5.0
                self._image.close()
            self._close = False
        self._image = None

    @property
    def level_count(self):
        """The number of levels in the image."""
        return 1

    @property
    def level_dimensions(self):
        """A list of (width, height) tuples, one for each level of the image.

        level_dimensions[n] contains the dimensions of level n."""
        return (self._image.size,)

    @property
    def level_downsamples(self):
        """A list of downsampling factors for each level of the image.

        level_downsample[n] contains the downsample factor of level n."""
        return (1.0,)

    @property
    def properties(self):
        """Metadata about the image.

        This is a map: property name -> property value."""
        return {}

    @property
    def associated_images(self):
        """Images associated with this whole-slide image.

        This is a map: image name -> PIL.Image."""
        return {}

    def get_best_level_for_downsample(self, _downsample):
        """Return the best level for displaying the given downsample."""
        return 0

    def read_region(self, location, level, size):
        """Return a PIL.Image containing the contents of the region.

        location: (x, y) tuple giving the top left pixel in the level 0
                  reference frame.
        level:    the level number.
        size:     (width, height) tuple giving the region size."""
        if level != 0:
            raise OpenSlideError("Invalid level")
        if ['fail' for s in size if s < 0]:
            raise OpenSlideError("Size %s must be non-negative" % (size,))
        # Any corner of the requested region may be outside the bounds of
        # the image.  Create a transparent tile of the correct size and
        # paste the valid part of the region into the correct location.
        image_topleft = [max(0, min(l, limit - 1))
                    for l, limit in zip(location, self._image.size)]
        image_bottomright = [max(0, min(l + s - 1, limit - 1))
                    for l, s, limit in zip(location, size, self._image.size)]
        tile = Image.new("RGBA", size, (0,) * 4)
        if not ['fail' for tl, br in zip(image_topleft, image_bottomright)
                if br - tl < 0]:  # "< 0" not a typo
            # Crop size is greater than zero in both dimensions.
            # PIL thinks the bottom right is the first *excluded* pixel
            crop = self._image.crop(image_topleft +
                    [d + 1 for d in image_bottomright])
            tile_offset = tuple(il - l for il, l in
                    zip(image_topleft, location))
            tile.paste(crop, tile_offset)
        return tile


def open_slide(filename):
    """Open a whole-slide or regular image.

    Return an OpenSlide object for whole-slide images and an ImageSlide
    object for other types of images."""
    try:
        return OpenSlide(filename)
    except OpenSlideUnsupportedFormatError:
        return ImageSlide(filename)


if __name__ == '__main__':
    import sys
    print("OpenSlide vendor:", OpenSlide.detect_format(sys.argv[1]))
    print("PIL format:", ImageSlide.detect_format(sys.argv[1]))
    with open_slide(sys.argv[1]) as _slide:
        print("Dimensions:", _slide.dimensions)
        print("Levels:", _slide.level_count)
        print("Level dimensions:", _slide.level_dimensions)
        print("Level downsamples:", _slide.level_downsamples)
        print("Properties:", _slide.properties)
        print("Associated images:", _slide.associated_images)
