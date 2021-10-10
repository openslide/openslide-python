================
OpenSlide Python
================

OpenSlide Python is a Python interface to the OpenSlide library.

OpenSlide_ is a C library that provides a simple interface for reading
whole-slide images, also known as virtual slides, which are high-resolution
images used in digital pathology.  These images can occupy tens of gigabytes
when uncompressed, and so cannot be easily read using standard tools or
libraries, which are designed for images that can be comfortably
uncompressed into RAM.  Whole-slide images are typically multi-resolution;
OpenSlide allows reading a small amount of image data at the resolution
closest to a desired zoom level.

OpenSlide can read virtual slides in several formats:

* Aperio_ (``.svs``, ``.tif``)
* Hamamatsu_ (``.ndpi``, ``.vms``, ``.vmu``)
* Leica_ (``.scn``)
* MIRAX_ (``.mrxs``)
* Philips_ (``.tiff``)
* Sakura_ (``.svslide``)
* Trestle_ (``.tif``)
* Ventana_ (``.bif``, ``.tif``)
* `Generic tiled TIFF`_ (``.tif``)

.. _OpenSlide: https://openslide.org/
.. _Aperio: https://openslide.org/formats/aperio/
.. _Hamamatsu: https://openslide.org/formats/hamamatsu/
.. _Leica: https://openslide.org/formats/leica/
.. _MIRAX: https://openslide.org/formats/mirax/
.. _Philips: https://openslide.org/formats/philips/
.. _Sakura: https://openslide.org/formats/sakura/
.. _Trestle: https://openslide.org/formats/trestle/
.. _Ventana: https://openslide.org/formats/ventana/
.. _`Generic tiled TIFF`: https://openslide.org/formats/generic-tiff/


Requirements
============

* Python 2 >= 2.6 or Python 3 >= 3.3
* OpenSlide >= 3.4.0
* Python Imaging Library or Pillow


Installation
============

1.  `Install OpenSlide`_.

2.  ``pip install openslide-python``

.. _`Install OpenSlide`: https://openslide.org/download/


Using PIL
---------

``setup.py`` assumes that you want to use the Pillow fork of PIL.  If you
already have classic PIL installed, you can use it instead.  Install
OpenSlide Python with:

::

  pip install --no-deps openslide-python

or, if you are installing by hand:

::

  python setup.py install --single-version-externally-managed --record /dev/null


More Information
================

- `API documentation`_
- Changelog_
- Website_
- GitHub_
- `Sample data`_

.. _`API documentation`: https://openslide.org/api/python/
.. _Changelog: https://raw.github.com/openslide/openslide-python/master/CHANGELOG.txt
.. _Website: https://openslide.org/
.. _GitHub: https://github.com/openslide/openslide-python
.. _`Sample data`: http://openslide.cs.cmu.edu/download/openslide-testdata/


License
=======

OpenSlide Python is released under the terms of the `GNU Lesser General
Public License, version 2.1`_.

.. _`GNU Lesser General Public License, version 2.1`: https://raw.github.com/openslide/openslide-python/master/lgpl-2.1.txt
