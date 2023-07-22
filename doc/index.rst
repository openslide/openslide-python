================
OpenSlide Python
================

OpenSlide Python is a Python interface to the OpenSlide_ library.

OpenSlide is a C library that provides a simple interface for reading
whole-slide images, also known as virtual slides, which are high-resolution
images used in digital pathology.  These images can occupy tens of gigabytes
when uncompressed, and so cannot be easily read using standard tools or
libraries, which are designed for images that can be comfortably
uncompressed into RAM.  Whole-slide images are typically multi-resolution;
OpenSlide allows reading a small amount of image data at the resolution
closest to a desired zoom level.

OpenSlide can read virtual slides in several formats:

* Aperio_ (``.svs``, ``.tif``)
* DICOM_ (``.dcm``)
* Hamamatsu_ (``.ndpi``, ``.vms``, ``.vmu``)
* Leica_ (``.scn``)
* MIRAX_ (``.mrxs``)
* Philips_ (``.tiff``)
* Sakura_ (``.svslide``)
* Trestle_ (``.tif``)
* Ventana_ (``.bif``, ``.tif``)
* `Generic tiled TIFF`_ (``.tif``)

OpenSlide Python is released under the terms of the `GNU Lesser General
Public License, version 2.1`_.

.. _OpenSlide: https://openslide.org/
.. _Aperio: https://openslide.org/formats/aperio/
.. _DICOM: https://openslide.org/formats/dicom/
.. _Hamamatsu: https://openslide.org/formats/hamamatsu/
.. _Leica: https://openslide.org/formats/leica/
.. _MIRAX: https://openslide.org/formats/mirax/
.. _Philips: https://openslide.org/formats/philips/
.. _Sakura: https://openslide.org/formats/sakura/
.. _Trestle: https://openslide.org/formats/trestle/
.. _Ventana: https://openslide.org/formats/ventana/
.. _`Generic tiled TIFF`: https://openslide.org/formats/generic-tiff/
.. _`GNU Lesser General Public License, version 2.1`: https://openslide.org/license/


Installing
==========

OpenSlide Python requires OpenSlide_, which must be installed separately.

On Linux and macOS, the easiest way to get both components is to install_
with a package manager that packages both, such as Anaconda_, DNF or Apt on
Linux systems, or MacPorts_ on macOS systems.  You can also install
OpenSlide Python with pip_ after installing OpenSlide with a package manager
or from source_.  Except for pip, do not mix OpenSlide and OpenSlide Python
from different package managers (for example, OpenSlide from MacPorts and
OpenSlide Python from Anaconda), since you'll get library conflicts.

On Windows, download the OpenSlide `Windows binaries`_ and extract them
to a known path.  Then, import ``openslide`` inside a
``with os.add_dll_directory()`` statement::

    # The path can also be read from a config file, etc.
    OPENSLIDE_PATH = r'c:\path\to\openslide-win64\bin'

    import os
    if hasattr(os, 'add_dll_directory'):
        # Windows
        with os.add_dll_directory(OPENSLIDE_PATH):
            import openslide
    else:
        import openslide

.. _install: https://openslide.org/download/#distribution-packages
.. _Anaconda: https://anaconda.org/
.. _MacPorts: https://www.macports.org/
.. _pip: https://pip.pypa.io/en/stable/
.. _source: https://openslide.org/download/#source
.. _`Windows binaries`: https://openslide.org/download/#windows-binaries


Basic usage
===========

OpenSlide objects
-----------------

.. module:: openslide

.. class:: OpenSlide(filename)

   An open whole-slide image.

   If any operation on the object fails, :exc:`OpenSlideError` is raised.
   OpenSlide has latching error semantics: once :exc:`OpenSlideError` is
   raised, all future operations on the :class:`OpenSlide`, other than
   :meth:`close()`, will also raise :exc:`OpenSlideError`.

   :meth:`close()` is called automatically when the object is deleted.
   The object may be used as a context manager, in which case it will be
   closed upon exiting the context.

   :param str filename: the file to open
   :raises OpenSlideUnsupportedFormatError: if the file is not recognized by
      OpenSlide
   :raises OpenSlideError: if the file is recognized but an error occurred

   .. classmethod:: detect_format(filename)

      Return a string describing the format vendor of the specified file.
      This string is also accessible via the :data:`PROPERTY_NAME_VENDOR`
      property.

      If the file is not recognized, return :obj:`None`.

      :param str filename: the file to examine

   .. attribute:: level_count

      The number of levels in the slide.  Levels are numbered from ``0``
      (highest resolution) to ``level_count - 1`` (lowest resolution).

   .. attribute:: dimensions

      A ``(width, height)`` tuple for level 0 of the slide.

   .. attribute:: level_dimensions

      A list of ``(width, height)`` tuples, one for each level of the slide.
      ``level_dimensions[k]`` are the dimensions of level ``k``.

   .. attribute:: level_downsamples

      A list of downsample factors for each level of the slide.
      ``level_downsamples[k]`` is the downsample factor of level ``k``.

   .. attribute:: properties

      Metadata about the slide, in the form of a
      :class:`~collections.abc.Mapping` from OpenSlide property name to
      property value.  Property values are always strings.  OpenSlide
      provides some :ref:`standard-properties`, plus
      additional properties that vary by slide format.

   .. attribute:: associated_images

      Images, such as label or macro images, which are associated with this
      slide.  This is a :class:`~collections.abc.Mapping` from image
      name to RGBA :class:`Image <PIL.Image.Image>`.

      Unlike in the C interface, these images are not premultiplied.

   .. attribute:: color_profile

      The embedded :ref:`color profile <color-management>` for this slide,
      as a Pillow :class:`~PIL.ImageCms.ImageCmsProfile`, or :obj:`None` if
      not available.

   .. method:: read_region(location, level, size)

      Return an RGBA :class:`Image <PIL.Image.Image>` containing the
      contents of the specified region.

      Unlike in the C interface, the image data is not premultiplied.

      :param tuple location: ``(x, y)`` tuple giving the top left pixel in
         the level 0 reference frame
      :param int level: the level number
      :param tuple size: ``(width, height)`` tuple giving the region size

   .. method:: get_best_level_for_downsample(downsample)

      Return the best level for displaying the given downsample.

      :param float downsample: the desired downsample factor

   .. method:: get_thumbnail(size)

      Return an :class:`Image <PIL.Image.Image>` containing an RGB thumbnail
      of the slide.

      :param tuple size: the maximum size of the thumbnail as a
         ``(width, height)`` tuple

   .. method:: set_cache(cache)

      Use the specified :class:`OpenSlideCache` to store recently decoded
      slide tiles.  By default, the :class:`OpenSlide` has a private cache
      with a default size.

      :param OpenSlideCache cache: a cache object
      :raises OpenSlideVersionError: if OpenSlide is older than version 4.0.0

   .. method:: close()

      Close the OpenSlide object.


.. _color-management:

Color management
----------------

Every slide region, associated image, thumbnail, and Deep Zoom tile produced
by OpenSlide Python includes a reference to an ICC color profile whenever a
profile is available for the underlying pixel data.  Profiles are stored as
a :class:`bytes` object in
:attr:`Image.info <PIL.Image.Image.info>`:attr:`['icc_profile']`.  If no
profile is available, the :attr:`icc_profile` dictionary key is absent.

To include the profile in an image file when saving the image to disk::

    image.save(filename, icc_profile=image.info.get('icc_profile'))

To perform color conversions using the profile, import it into
:mod:`ImageCms <PIL.ImageCms>`.  For example, to convert an image in-place
to a synthesized sRGB profile, using absolute colorimetric rendering::

    from io import BytesIO
    from PIL import ImageCms

    fromProfile = ImageCms.getOpenProfile(BytesIO(image.info['icc_profile']))
    toProfile = ImageCms.createProfile('sRGB')
    ImageCms.profileToProfile(
        image, fromProfile, toProfile,
        ImageCms.Intent.ABSOLUTE_COLORIMETRIC, 'RGBA', True, 0
    )

Absolute colorimetric rendering `maximizes the comparability`_ of images
produced by different scanners.  When converting Deep Zoom tiles, use
``'RGB'`` instead of ``'RGBA'``.

All pyramid regions in a slide have the same profile, but each associated
image can have its own profile.  As a convenience, the former is also
available as :attr:`OpenSlide.color_profile`, already parsed into an
:class:`~PIL.ImageCms.ImageCmsProfile` object.  You can save processing time
by building an :class:`~PIL.ImageCms.ImageCmsTransform` for the slide and
reusing it for multiple slide regions::

    toProfile = ImageCms.createProfile('sRGB')
    transform = ImageCms.buildTransform(
        slide.color_profile, toProfile, 'RGBA', 'RGBA',
        ImageCms.Intent.ABSOLUTE_COLORIMETRIC, 0
    )
    # for each region image:
    ImageCms.applyTransform(image, transform, True)

.. _maximizes the comparability: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4478790/


Caching
-------

.. class:: OpenSlideCache(capacity)

   An in-memory tile cache.

   Tile caches can be attached to one or more :class:`OpenSlide` objects
   with :meth:`OpenSlide.set_cache` to cache recently-decoded tiles.  By
   default, each :class:`OpenSlide` has its own cache with a default size.

   :param int capacity: the cache capacity in bytes
   :raises OpenSlideVersionError: if OpenSlide is older than version 4.0.0


.. _standard-properties:

Standard properties
-------------------

The :mod:`openslide` module provides attributes containing the names of
some commonly-used OpenSlide properties.

.. data:: PROPERTY_NAME_COMMENT

   The name of the property containing a slide's comment, if any.

.. data:: PROPERTY_NAME_VENDOR

   The name of the property containing an identification of the vendor.

.. data:: PROPERTY_NAME_QUICKHASH1

   The name of the property containing the "quickhash-1" sum.

.. data:: PROPERTY_NAME_BACKGROUND_COLOR

   The name of the property containing a slide's background color, if any.
   It is represented as an RGB hex triplet.

.. data:: PROPERTY_NAME_OBJECTIVE_POWER

   The name of the property containing a slide's objective power, if known.

.. data:: PROPERTY_NAME_MPP_X

   The name of the property containing the number of microns per pixel in
   the X dimension of level 0, if known.

.. data:: PROPERTY_NAME_MPP_Y

   The name of the property containing the number of microns per pixel in
   the Y dimension of level 0, if known.

.. data:: PROPERTY_NAME_BOUNDS_X

   The name of the property containing the X coordinate of the rectangle
   bounding the non-empty region of the slide, if available.

.. data:: PROPERTY_NAME_BOUNDS_Y

   The name of the property containing the Y coordinate of the rectangle
   bounding the non-empty region of the slide, if available.

.. data:: PROPERTY_NAME_BOUNDS_WIDTH

   The name of the property containing the width of the rectangle bounding
   the non-empty region of the slide, if available.

.. data:: PROPERTY_NAME_BOUNDS_HEIGHT

   The name of the property containing the height of the rectangle bounding
   the non-empty region of the slide, if available.


Exceptions
----------

.. exception:: OpenSlideError

   An error produced by the OpenSlide library.

   Once :exc:`OpenSlideError` has been raised by a particular
   :class:`OpenSlide`, all future operations on that :class:`OpenSlide`
   (other than :meth:`close() <OpenSlide.close>`) will also raise
   :exc:`OpenSlideError`.

.. exception:: OpenSlideUnsupportedFormatError

   OpenSlide does not support the requested file.  Subclass of
   :exc:`OpenSlideError`.

.. exception:: OpenSlideVersionError

   This version of OpenSlide does not support the requested functionality.
   Subclass of :exc:`OpenSlideError`.


.. _wrapping-a-pil-image:

Wrapping a Pillow Image
=======================

.. class:: ImageSlide(file)

   A wrapper around an :class:`Image <PIL.Image.Image>` object that
   provides an :class:`OpenSlide`-compatible API.

   :param file: a filename or :class:`Image <PIL.Image.Image>` object
   :raises OSError: if the file cannot be opened

.. function:: open_slide(filename)

   Return an :class:`OpenSlide` for whole-slide images and an
   :class:`ImageSlide` for other types of images.

   :param str filename: the file to open
   :raises OpenSlideError: if the file is recognized by OpenSlide but an
      error occurred
   :raises OSError: if the file is not recognized at all


Deep Zoom support
=================

.. module:: openslide.deepzoom

OpenSlide Python provides functionality for generating individual
`Deep Zoom`_ tiles from slide objects.  This is useful for displaying
whole-slide images in a web browser without converting the entire slide to
Deep Zoom or a similar format.

.. _`Deep Zoom`: https://docs.microsoft.com/en-us/previous-versions/windows/silverlight/dotnet-windows-silverlight/cc645050(v=vs.95)

.. class:: DeepZoomGenerator(osr, tile_size=254, overlap=1, limit_bounds=False)

   A Deep Zoom generator that wraps an
   :class:`OpenSlide <openslide.OpenSlide>` or
   :class:`ImageSlide <openslide.ImageSlide>` object.

   :param osr: the slide object
   :param int tile_size: the width and height of a single tile.  For best
      viewer performance, ``tile_size + 2 * overlap`` should be a power of two.
   :param int overlap: the number of extra pixels to add to each interior edge
      of a tile
   :param bool limit_bounds: ``True`` to render only the non-empty slide
      region

   .. attribute:: level_count

      The number of Deep Zoom levels in the image.

   .. attribute:: tile_count

      The total number of Deep Zoom tiles in the image.

   .. attribute:: level_tiles

      A list of ``(tiles_x, tiles_y)`` tuples for each Deep Zoom level.
      ``level_tiles[k]`` are the tile counts of level ``k``.

   .. attribute:: level_dimensions

      A list of ``(pixels_x, pixels_y)`` tuples for each Deep Zoom level.
      ``level_dimensions[k]`` are the dimensions of level ``k``.

   .. method:: get_dzi(format)

      Return a string containing the XML metadata for the Deep Zoom ``.dzi``
      file.

      :param str format: the delivery format of the individual tiles
         (``png`` or ``jpeg``)

   .. method:: get_tile(level, address)

      Return an RGB :class:`Image <PIL.Image.Image>` for a tile.

      :param int level: the Deep Zoom level
      :param tuple address: the address of the tile within the level as a
         ``(column, row)`` tuple

   .. method:: get_tile_coordinates(level, address)

      Return the :meth:`OpenSlide.read_region()
      <openslide.OpenSlide.read_region>` arguments corresponding to the
      specified tile.

      Most applications should use :meth:`get_tile()` instead.

      :param int level: the Deep Zoom level
      :param tuple address: the address of the tile within the level as a
         ``(column, row)`` tuple

   .. method:: get_tile_dimensions(level, address)

      Return a ``(pixels_x, pixels_y)`` tuple for the specified tile.

      :param int level: the Deep Zoom level
      :param tuple address: the address of the tile within the level as a
         ``(column, row)`` tuple


Example programs
----------------

Several `Deep Zoom examples`_ are included with OpenSlide Python:

deepzoom_server.py_
  A basic server for a single slide.  It serves a web page with a zoomable
  slide viewer, a list of slide properties, and the ability to view
  associated images.

deepzoom_multiserver.py_
  A basic server for a directory tree of slides.  It serves an index page
  which links to zoomable slide viewers for all slides in the tree.

deepzoom_tile.py_
  A program to generate and store a complete Deep Zoom directory tree for a
  slide.  It can optionally store an HTML page with a zoomable slide viewer,
  a list of slide properties, and the ability to view associated images.

  This program is intended as an example.  If you need to generate Deep Zoom
  trees for production applications, consider `using VIPS`_ instead.

.. _`Deep Zoom examples`: https://github.com/openslide/openslide-python/tree/main/examples/deepzoom
.. _deepzoom_server.py: https://github.com/openslide/openslide-python/blob/main/examples/deepzoom/deepzoom_server.py
.. _deepzoom_multiserver.py: https://github.com/openslide/openslide-python/blob/main/examples/deepzoom/deepzoom_multiserver.py
.. _deepzoom_tile.py: https://github.com/openslide/openslide-python/blob/main/examples/deepzoom/deepzoom_tile.py
.. _`using VIPS`: https://github.com/openslide/openslide/wiki/OpenSlideAndVIPS
