# Notable Changes in OpenSlide Python

## Version 1.4.0, 2024-10-29

### New features

* Support OpenSlide [installed from PyPI][] with `pip install openslide-bin`
* Add type hints for Python ≥ 3.10
* Add wheels for Linux aarch64, Linux x86_64, and macOS arm64 + x86_64
* Build version-independent wheels on Python ≥ 3.11
* examples: Default `deepzoom_tile.py` job count to available CPUs when known

### Changes

* Drop wheel for 32-bit Windows
* Require `AbstractSlide` subclasses to implement all abstract methods
* Provide default `AbstractSlide.set_cache()` implementation
* Switch to [PEP 621][] project metadata
* docs: Document existence of `AbstractSlide`
* examples: Update OpenSeadragon to 5.0.0

### Bug fixes

* If OpenSlide cannot be loaded, report errors from all attempts
* Fix `OpenSlide` support for `bytes` filename arguments (1.2.0 regression)
* Disallow arbitrary types as `OpenSlide` filename arguments (1.2.0 regression)
* Encode `OpenSlide` filename arguments using [Python filesystem encoding][]
* Add error check to `OpenSlide.set_cache()`
* docs: Fix types of properties that return tuples of items

[installed from PyPI]: https://pypi.org/project/openslide-bin/
[PEP 621]: https://peps.python.org/pep-0621/
[Python filesystem encoding]: https://docs.python.org/3/glossary.html#term-filesystem-encoding-and-error-handler


## Version 1.3.1, 2023-10-08

* docs: Document using ICC profile's default intent, not absolute colorimetric
* examples: Default to ICC profile's default intent, not absolute colorimetric
* tests: Correctly require pytest ≥ 7.0


## Version 1.3.0, 2023-07-22

* Support new soname in OpenSlide ≥ 4.0.0
* Drop support for Python 3.7
* Expose color management profiles where available
* Notate available OpenSlide functions in low-level API
* docs: Update OpenSlide 3.5.0 references to 4.0.0
* docs: Consolidate license information
* docs: Drop support for building with Sphinx \< 1.6
* examples: Fix startup failure with Flask ≥ 2.3.0
* examples: Transform to sRGB (with absolute colorimetric intent) by default
* examples: Update OpenSeadragon to 4.1.0
* examples: Correctly import `openslide` on Windows if `OPENSLIDE_PATH` not set
* tests: Fix `pytest` of installed package from source directory


## Version 1.2.0, 2022-06-17

* Drop support for Python \< 3.7
* Support cache customization with OpenSlide 3.5.0
* Improve pixel read performance
* Clarify exception raised on Windows or macOS when OpenSlide can't be found
* Raise `OpenSlideVersionError` when an operation requires a newer OpenSlide
* Support `pathlib.Path` in filename arguments
* Fix Pillow `Image.ANTIALIAS` deprecation warning
* docs: Add detailed installation instructions
* docs: Convert `README` and `CHANGELOG` to Markdown
* examples: Share cache among all multiserver slides, if supported
* examples: Fix `deepzoom_tile.py --viewer` with Jinja 3.x
* examples: Read OpenSlide DLL path from `OPENSLIDE_PATH` env var on Windows
* examples: Update OpenSeadragon to 3.0.0


## Version 1.1.2, 2020-09-13

* Fix install with setuptools ≥ 46
* Fix `ImportError` with Python 3.9
* Fix docs build with Sphinx 2.x
* Remove `--without-performance` install option


## Version 1.1.1, 2016-06-11

* Change default Deep Zoom tile size to 254 pixels
* Fix image reading with Pillow 3.x when installed `--without-performance`
* Fix reading ≥ 2<sup>29</sup> pixels per call `--without-performance`
* Fix some `unclosed file` ResourceWarnings on Python 3
* Improve object reprs
* Add test suite
* examples: Drop support for Internet Explorer \< 9


## Version 1.1.0, 2015-04-20

* Improve pixel read performance using optional extension module
* examples: Add scale bar via OpenSeadragonScalebar plugin
* examples: Update OpenSeadragon to 1.2.1
* examples: Enable rotation buttons in multiserver
* examples: Verify at server startup that file was specified
* examples: Disable pinch zoom outside of viewer


## Version 1.0.1, 2014-03-09

* Fix documentation build breakage


## Version 1.0.0, 2014-03-09

* Add documentation
* Switch from distutils to setuptools
* Declare Pillow dependency in `setup.py` (but still support PIL)


## Version 0.5.1, 2014-01-26

* Fix breakage on Python 2.6
* examples: Fix tile server breakage on classic PIL


## Version 0.5.0, 2014-01-25

* Require OpenSlide 3.4.0
* Support Python 3
* Return Unicode strings on Python 2
* Replace `OpenSlide.can_open()` with `OpenSlide.detect_format()`
* Optionally generate Deep Zoom tiles only for the non-empty slide region
* Fix Deep Zoom tile positioning bug affecting Aperio slides
* Fix library loading with MacPorts
* Propagate open errors from `openslide.open_slide()`
* examples: Add multiple-slide Deep Zoom server
* examples: Enable multithreading in tile servers
* examples: Avoid loading smallest Deep Zoom levels
* examples: Update OpenSeadragon to 1.0.0


## Version 0.4.0, 2012-09-08

* Require OpenSlide 3.3.0
* Rename `layer` to `level` throughout API
* Provide OpenSlide version in `openslide.__library_version__`
* Properly report `openslide_open()` errors on OpenSlide 3.3.0
* Fix library loading on Mac OS X


## Version 0.3.0, 2011-12-16

* Fix segfault if properties/associated images accessed after `OpenSlide`
  is closed
* Add methods to get Deep Zoom tile coordinates and dimensions
* Fix loading libopenslide on Windows
* Fix for large JPEG tiles in example Deep Zoom tilers
* Make example static tiler output self-contained


## Version 0.2.0, 2011-09-02

* Initial library release
* Example static Deep Zoom tiler and web viewer applications
