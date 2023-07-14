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

"""Support for Deep Zoom images.

This module provides functionality for generating Deep Zoom images from
OpenSlide objects.
"""

from io import BytesIO
import math
from xml.etree.ElementTree import Element, ElementTree, SubElement

from PIL import Image

import openslide


class DeepZoomGenerator:
    """Generates Deep Zoom tiles and metadata."""

    BOUNDS_OFFSET_PROPS = (
        openslide.PROPERTY_NAME_BOUNDS_X,
        openslide.PROPERTY_NAME_BOUNDS_Y,
    )
    BOUNDS_SIZE_PROPS = (
        openslide.PROPERTY_NAME_BOUNDS_WIDTH,
        openslide.PROPERTY_NAME_BOUNDS_HEIGHT,
    )

    def __init__(self, osr, tile_size=254, overlap=1, limit_bounds=False):
        """Create a DeepZoomGenerator wrapping an OpenSlide object.

        osr:          a slide object.
        tile_size:    the width and height of a single tile.  For best viewer
                      performance, tile_size + 2 * overlap should be a power
                      of two.
        overlap:      the number of extra pixels to add to each interior edge
                      of a tile.
        limit_bounds: True to render only the non-empty slide region."""

        # We have four coordinate planes:
        # - Row and column of the tile within the Deep Zoom level (t_)
        # - Pixel coordinates within the Deep Zoom level (z_)
        # - Pixel coordinates within the slide level (l_)
        # - Pixel coordinates within slide level 0 (l0_)

        self._osr = osr
        self._z_t_downsample = tile_size
        self._z_overlap = overlap
        self._limit_bounds = limit_bounds

        # Precompute dimensions
        # Slide level and offset
        if limit_bounds:
            # Level 0 coordinate offset
            self._l0_offset = tuple(
                int(osr.properties.get(prop, 0)) for prop in self.BOUNDS_OFFSET_PROPS
            )
            # Slide level dimensions scale factor in each axis
            size_scale = tuple(
                int(osr.properties.get(prop, l0_lim)) / l0_lim
                for prop, l0_lim in zip(self.BOUNDS_SIZE_PROPS, osr.dimensions)
            )
            # Dimensions of active area
            self._l_dimensions = tuple(
                tuple(
                    int(math.ceil(l_lim * scale))
                    for l_lim, scale in zip(l_size, size_scale)
                )
                for l_size in osr.level_dimensions
            )
        else:
            self._l_dimensions = osr.level_dimensions
            self._l0_offset = (0, 0)
        self._l0_dimensions = self._l_dimensions[0]
        # Deep Zoom level
        z_size = self._l0_dimensions
        z_dimensions = [z_size]
        while z_size[0] > 1 or z_size[1] > 1:
            z_size = tuple(max(1, int(math.ceil(z / 2))) for z in z_size)
            z_dimensions.append(z_size)
        self._z_dimensions = tuple(reversed(z_dimensions))

        # Tile
        def tiles(z_lim):
            return int(math.ceil(z_lim / self._z_t_downsample))

        self._t_dimensions = tuple(
            (tiles(z_w), tiles(z_h)) for z_w, z_h in self._z_dimensions
        )

        # Deep Zoom level count
        self._dz_levels = len(self._z_dimensions)

        # Total downsamples for each Deep Zoom level
        l0_z_downsamples = tuple(
            2 ** (self._dz_levels - dz_level - 1) for dz_level in range(self._dz_levels)
        )

        # Preferred slide levels for each Deep Zoom level
        self._slide_from_dz_level = tuple(
            self._osr.get_best_level_for_downsample(d) for d in l0_z_downsamples
        )

        # Piecewise downsamples
        self._l0_l_downsamples = self._osr.level_downsamples
        self._l_z_downsamples = tuple(
            l0_z_downsamples[dz_level]
            / self._l0_l_downsamples[self._slide_from_dz_level[dz_level]]
            for dz_level in range(self._dz_levels)
        )

        # Slide background color
        self._bg_color = '#' + self._osr.properties.get(
            openslide.PROPERTY_NAME_BACKGROUND_COLOR, 'ffffff'
        )

    def __repr__(self):
        return '{}({!r}, tile_size={!r}, overlap={!r}, limit_bounds={!r})'.format(
            self.__class__.__name__,
            self._osr,
            self._z_t_downsample,
            self._z_overlap,
            self._limit_bounds,
        )

    @property
    def level_count(self):
        """The number of Deep Zoom levels in the image."""
        return self._dz_levels

    @property
    def level_tiles(self):
        """A list of (tiles_x, tiles_y) tuples for each Deep Zoom level."""
        return self._t_dimensions

    @property
    def level_dimensions(self):
        """A list of (pixels_x, pixels_y) tuples for each Deep Zoom level."""
        return self._z_dimensions

    @property
    def tile_count(self):
        """The total number of Deep Zoom tiles in the image."""
        return sum(t_cols * t_rows for t_cols, t_rows in self._t_dimensions)

    def get_tile(self, level, address):
        """Return an RGB PIL.Image for a tile.

        level:     the Deep Zoom level.
        address:   the address of the tile within the level as a (col, row)
                   tuple."""

        # Read tile
        args, z_size = self._get_tile_info(level, address)
        tile = self._osr.read_region(*args)
        profile = tile.info.get('icc_profile')

        # Apply on solid background
        bg = Image.new('RGB', tile.size, self._bg_color)
        tile = Image.composite(tile, bg, tile)

        # Scale to the correct size
        if tile.size != z_size:
            # Image.Resampling added in Pillow 9.1.0
            # Image.LANCZOS removed in Pillow 10
            tile.thumbnail(z_size, getattr(Image, 'Resampling', Image).LANCZOS)

        # Reference ICC profile
        if profile is not None:
            tile.info['icc_profile'] = profile

        return tile

    def _get_tile_info(self, dz_level, t_location):
        # Check parameters
        if dz_level < 0 or dz_level >= self._dz_levels:
            raise ValueError("Invalid level")
        for t, t_lim in zip(t_location, self._t_dimensions[dz_level]):
            if t < 0 or t >= t_lim:
                raise ValueError("Invalid address")

        # Get preferred slide level
        slide_level = self._slide_from_dz_level[dz_level]

        # Calculate top/left and bottom/right overlap
        z_overlap_tl = tuple(self._z_overlap * int(t != 0) for t in t_location)
        z_overlap_br = tuple(
            self._z_overlap * int(t != t_lim - 1)
            for t, t_lim in zip(t_location, self.level_tiles[dz_level])
        )

        # Get final size of the tile
        z_size = tuple(
            min(self._z_t_downsample, z_lim - self._z_t_downsample * t) + z_tl + z_br
            for t, z_lim, z_tl, z_br in zip(
                t_location, self._z_dimensions[dz_level], z_overlap_tl, z_overlap_br
            )
        )

        # Obtain the region coordinates
        z_location = [self._z_from_t(t) for t in t_location]
        l_location = [
            self._l_from_z(dz_level, z - z_tl)
            for z, z_tl in zip(z_location, z_overlap_tl)
        ]
        # Round location down and size up, and add offset of active area
        l0_location = tuple(
            int(self._l0_from_l(slide_level, l) + l0_off)
            for l, l0_off in zip(l_location, self._l0_offset)
        )
        l_size = tuple(
            int(min(math.ceil(self._l_from_z(dz_level, dz)), l_lim - math.ceil(l)))
            for l, dz, l_lim in zip(l_location, z_size, self._l_dimensions[slide_level])
        )

        # Return read_region() parameters plus tile size for final scaling
        return ((l0_location, slide_level, l_size), z_size)

    def _l0_from_l(self, slide_level, l):
        return self._l0_l_downsamples[slide_level] * l

    def _l_from_z(self, dz_level, z):
        return self._l_z_downsamples[dz_level] * z

    def _z_from_t(self, t):
        return self._z_t_downsample * t

    def get_tile_coordinates(self, level, address):
        """Return the OpenSlide.read_region() arguments for the specified tile.

        Most users should call get_tile() rather than calling
        OpenSlide.read_region() directly.

        level:     the Deep Zoom level.
        address:   the address of the tile within the level as a (col, row)
                   tuple."""
        return self._get_tile_info(level, address)[0]

    def get_tile_dimensions(self, level, address):
        """Return a (pixels_x, pixels_y) tuple for the specified tile.

        level:     the Deep Zoom level.
        address:   the address of the tile within the level as a (col, row)
                   tuple."""
        return self._get_tile_info(level, address)[1]

    def get_dzi(self, format):
        """Return a string containing the XML metadata for the .dzi file.

        format:    the format of the individual tiles ('png' or 'jpeg')"""
        image = Element(
            'Image',
            TileSize=str(self._z_t_downsample),
            Overlap=str(self._z_overlap),
            Format=format,
            xmlns='http://schemas.microsoft.com/deepzoom/2008',
        )
        w, h = self._l0_dimensions
        SubElement(image, 'Size', Width=str(w), Height=str(h))
        tree = ElementTree(element=image)
        buf = BytesIO()
        tree.write(buf, encoding='UTF-8')
        return buf.getvalue().decode('UTF-8')
