#
# openslide-python - Python bindings for the OpenSlide library
#
# Copyright (c) 2016-2023 Benjamin Gilbert
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

from ctypes import ArgumentError
import re
import sys
import unittest

from PIL import Image
from common import file_path

from openslide import (
    OpenSlide,
    OpenSlideCache,
    OpenSlideError,
    OpenSlideUnsupportedFormatError,
    lowlevel,
)


class TestCache(unittest.TestCase):
    @unittest.skipUnless(lowlevel.cache_create.available, "requires OpenSlide 4.0.0")
    def test_create_cache(self):
        OpenSlideCache(0)
        OpenSlideCache(1)
        OpenSlideCache(4 << 20)
        self.assertRaises(ArgumentError, lambda: OpenSlideCache(-1))
        self.assertRaises(ArgumentError, lambda: OpenSlideCache(1.3))


class TestSlideWithoutOpening(unittest.TestCase):
    def test_detect_format(self):
        self.assertTrue(OpenSlide.detect_format(file_path('__missing_file')) is None)
        self.assertTrue(OpenSlide.detect_format(file_path('../setup.py')) is None)
        self.assertEqual(
            OpenSlide.detect_format(file_path('boxes.tiff')), 'generic-tiff'
        )

    def test_open(self):
        self.assertRaises(
            OpenSlideUnsupportedFormatError, lambda: OpenSlide('__does_not_exist')
        )
        self.assertRaises(
            OpenSlideUnsupportedFormatError, lambda: OpenSlide('setup.py')
        )
        self.assertRaises(OpenSlideUnsupportedFormatError, lambda: OpenSlide(None))
        self.assertRaises(OpenSlideUnsupportedFormatError, lambda: OpenSlide(3))
        self.assertRaises(
            OpenSlideUnsupportedFormatError, lambda: OpenSlide('unopenable.tiff')
        )

    def test_operations_on_closed_handle(self):
        osr = OpenSlide(file_path('boxes.tiff'))
        props = osr.properties
        associated = osr.associated_images
        osr.close()
        self.assertRaises(ArgumentError, lambda: osr.read_region((0, 0), 0, (100, 100)))
        self.assertRaises(ArgumentError, lambda: osr.close())
        self.assertRaises(ArgumentError, lambda: props['openslide.vendor'])
        self.assertRaises(ArgumentError, lambda: associated['label'])

    def test_context_manager(self):
        osr = OpenSlide(file_path('boxes.tiff'))
        with osr:
            self.assertEqual(osr.level_count, 4)
        self.assertRaises(ArgumentError, lambda: osr.level_count)


class _SlideTest:
    def setUp(self):
        self.osr = OpenSlide(file_path(self.FILENAME))

    def tearDown(self):
        self.osr.close()


class TestSlide(_SlideTest, unittest.TestCase):
    FILENAME = 'boxes.tiff'

    def test_repr(self):
        self.assertEqual(repr(self.osr), 'OpenSlide(%r)' % file_path('boxes.tiff'))

    def test_basic_metadata(self):
        self.assertEqual(self.osr.level_count, 4)
        self.assertEqual(
            self.osr.level_dimensions, ((300, 250), (150, 125), (75, 62), (37, 31))
        )
        self.assertEqual(self.osr.dimensions, (300, 250))

        self.assertEqual(len(self.osr.level_downsamples), self.osr.level_count)
        self.assertEqual(self.osr.level_downsamples[0:2], (1, 2))
        self.assertAlmostEqual(self.osr.level_downsamples[2], 4, places=0)
        self.assertAlmostEqual(self.osr.level_downsamples[3], 8, places=0)

        self.assertEqual(self.osr.get_best_level_for_downsample(0.5), 0)
        self.assertEqual(self.osr.get_best_level_for_downsample(3), 1)
        self.assertEqual(self.osr.get_best_level_for_downsample(37), 3)

    def test_properties(self):
        self.assertEqual(self.osr.properties['openslide.vendor'], 'generic-tiff')
        self.assertRaises(KeyError, lambda: self.osr.properties['__does_not_exist'])
        # test __len__ and __iter__
        self.assertEqual(
            len([v for v in self.osr.properties]), len(self.osr.properties)
        )
        self.assertEqual(
            repr(self.osr.properties), '<_PropertyMap %r>' % dict(self.osr.properties)
        )

    @unittest.skipUnless(
        lowlevel.read_icc_profile.available, "requires OpenSlide 4.0.0"
    )
    def test_color_profile(self):
        self.assertEqual(self.osr.color_profile.profile.device_class, 'mntr')
        self.assertEqual(
            len(self.osr.read_region((0, 0), 0, (100, 100)).info['icc_profile']), 588
        )
        self.assertEqual(
            len(self.osr.get_thumbnail((100, 100)).info['icc_profile']), 588
        )

    def test_read_region(self):
        self.assertEqual(
            self.osr.read_region((-10, -10), 1, (400, 400)).size, (400, 400)
        )

    def test_read_region_size_dimension_zero(self):
        self.assertEqual(self.osr.read_region((0, 0), 1, (400, 0)).size, (400, 0))

    def test_read_region_bad_level(self):
        self.assertEqual(self.osr.read_region((0, 0), 4, (100, 100)).size, (100, 100))

    def test_read_region_bad_size(self):
        self.assertRaises(
            OpenSlideError, lambda: self.osr.read_region((0, 0), 1, (400, -5))
        )

    @unittest.skipIf(sys.maxsize < 1 << 32, '32-bit Python')
    # Broken on Pillow < 6.2.0.
    # https://github.com/python-pillow/Pillow/issues/3963
    @unittest.skipIf(
        [int(i) for i in getattr(Image, '__version__', '0').split('.')] < [6, 2, 0],
        'broken on Pillow < 6.2.0',
    )
    # Disabled to avoid OOM killer on small systems, since the stdlib
    # doesn't provide a way to find out how much RAM we have
    def _test_read_region_2GB(self):
        self.assertEqual(
            self.osr.read_region((1000, 1000), 0, (32768, 16384)).size, (32768, 16384)
        )

    def test_thumbnail(self):
        self.assertEqual(self.osr.get_thumbnail((100, 100)).size, (100, 83))

    @unittest.skipUnless(lowlevel.cache_create.available, "requires OpenSlide 4.0.0")
    def test_set_cache(self):
        self.osr.set_cache(OpenSlideCache(64 << 10))
        self.assertEqual(self.osr.read_region((0, 0), 0, (400, 400)).size, (400, 400))
        self.assertRaises(TypeError, lambda: self.osr.set_cache(None))
        self.assertRaises(TypeError, lambda: self.osr.set_cache(3))


class TestAperioSlide(_SlideTest, unittest.TestCase):
    FILENAME = 'small.svs'

    def test_associated_images(self):
        self.assertEqual(self.osr.associated_images['thumbnail'].size, (16, 16))
        self.assertRaises(KeyError, lambda: self.osr.associated_images['__missing'])
        # test __len__ and __iter__
        self.assertEqual(
            len([v for v in self.osr.associated_images]),
            len(self.osr.associated_images),
        )

        def mangle_repr(o):
            return re.sub('0x[0-9a-fA-F]+', '(mangled)', repr(o))

        self.assertEqual(
            mangle_repr(self.osr.associated_images),
            '<_AssociatedImageMap %s>' % mangle_repr(dict(self.osr.associated_images)),
        )

    def test_color_profile(self):
        self.assertIsNone(self.osr.color_profile)
        self.assertNotIn(
            'icc_profile', self.osr.read_region((0, 0), 0, (100, 100)).info
        )
        self.assertNotIn('icc_profile', self.osr.associated_images['thumbnail'].info)
        self.assertNotIn('icc_profile', self.osr.get_thumbnail((100, 100)).info)


# Requires DICOM support in OpenSlide.  Use associated image ICC support as
# a proxy.
@unittest.skipUnless(
    lowlevel.read_associated_image_icc_profile.available, "requires OpenSlide 4.0.0"
)
class TestDicomSlide(_SlideTest, unittest.TestCase):
    FILENAME = 'boxes_0.dcm'

    def test_color_profile(self):
        self.assertEqual(self.osr.color_profile.profile.device_class, 'mntr')
        main_profile = self.osr.read_region((0, 0), 0, (100, 100)).info['icc_profile']
        associated_profile = self.osr.associated_images['thumbnail'].info['icc_profile']
        self.assertEqual(len(main_profile), 456)
        self.assertEqual(main_profile, associated_profile)
        self.assertIs(main_profile, associated_profile)


class TestUnreadableSlide(_SlideTest, unittest.TestCase):
    FILENAME = 'unreadable.svs'

    def test_read_bad_region(self):
        self.assertEqual(self.osr.properties['openslide.vendor'], 'aperio')
        self.assertRaises(
            OpenSlideError, lambda: self.osr.read_region((0, 0), 0, (16, 16))
        )
        # verify that errors are sticky
        self.assertRaises(
            OpenSlideError, lambda: self.osr.properties['openslide.vendor']
        )

    def test_read_bad_associated_image(self):
        self.assertEqual(self.osr.properties['openslide.vendor'], 'aperio')
        # Prints "JPEGLib: Bogus marker length." to stderr due to
        # https://github.com/openslide/openslide/issues/36
        self.assertRaises(
            OpenSlideError, lambda: self.osr.associated_images['thumbnail']
        )
        # verify that errors are sticky
        self.assertRaises(
            OpenSlideError, lambda: self.osr.properties['openslide.vendor']
        )
