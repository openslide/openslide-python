# OpenSlide Python

OpenSlide Python is a Python interface to the OpenSlide library.

[OpenSlide] is a C library that provides a simple interface for reading
whole-slide images, also known as virtual slides, which are high-resolution
images used in digital pathology.  These images can occupy tens of gigabytes
when uncompressed, and so cannot be easily read using standard tools or
libraries, which are designed for images that can be comfortably
uncompressed into RAM.  Whole-slide images are typically multi-resolution;
OpenSlide allows reading a small amount of image data at the resolution
closest to a desired zoom level.

OpenSlide can read virtual slides in several formats:

* [Aperio][]: (`.svs`, `.tif`)
* [Hamamatsu][]: (`.ndpi`, `.vms`, `.vmu`)
* [Leica][]: (`.scn`)
* [MIRAX][]: (`.mrxs`)
* [Philips][]: (`.tiff`)
* [Sakura][]: (`.svslide`)
* [Trestle][]: (`.tif`)
* [Ventana][]: (`.bif`, `.tif`)
* [Generic tiled TIFF][]: (`.tif`)

[OpenSlide]: https://openslide.org/
[Aperio]: https://openslide.org/formats/aperio/
[Hamamatsu]: https://openslide.org/formats/hamamatsu/
[Leica]: https://openslide.org/formats/leica/
[MIRAX]: https://openslide.org/formats/mirax/
[Philips]: https://openslide.org/formats/philips/
[Sakura]: https://openslide.org/formats/sakura/
[Trestle]: https://openslide.org/formats/trestle/
[Ventana]: https://openslide.org/formats/ventana/
[Generic tiled TIFF]: https://openslide.org/formats/generic-tiff/


## Requirements

* Python &ge; 3.7
* OpenSlide &ge; 3.4.0
* Pillow


## Installation

OpenSlide Python requires [OpenSlide].  For instructions on installing both
components so OpenSlide Python can find OpenSlide, see the package
[documentation][installing].

[installing]: https://openslide.org/api/python/#installing


## More Information

- [API documentation](https://openslide.org/api/python/)
- [Changelog](https://github.com/openslide/openslide-python/blob/main/CHANGELOG.md)
- [Website][OpenSlide]
- [GitHub](https://github.com/openslide/openslide-python)
- [Sample data](http://openslide.cs.cmu.edu/download/openslide-testdata/)


## License

OpenSlide Python is released under the terms of the [GNU Lesser General
Public License, version 2.1](https://raw.github.com/openslide/openslide-python/main/lgpl-2.1.txt).
