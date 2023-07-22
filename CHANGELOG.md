# Notable Changes in OpenSlide Python

## Version 1.3.0, 2023-07-22

* Support new soname in OpenSlide &ge; 4.0.0
* Drop support for Python 3.7
* Expose color management profiles where available
* Notate available OpenSlide functions in low-level API
* docs: Update OpenSlide 3.5.0 references to 4.0.0
* docs: Consolidate license information
* docs: Drop support for building with Sphinx &lt; 1.6
* examples: Fix startup failure with Flask &ge; 2.3.0
* examples: Transform to sRGB (with absolute colorimetric intent) by default
* examples: Update OpenSeadragon to 4.1.0
* examples: Correctly import `openslide` on Windows if `OPENSLIDE_PATH` not set
* tests: Fix `pytest` of installed package from source directory

## Version 1.2.0, 2022-06-17

* Drop support for Python &lt; 3.7
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

* Fix install with setuptools &ge; 46
* Fix `ImportError` with Python 3.9
* Fix docs build with Sphinx 2.x
* Remove `--without-performance` install option

## Version 1.1.1, 2016-06-11

* Change default Deep Zoom tile size to 254 pixels
* Fix image reading with Pillow 3.x when installed `--without-performance`
* Fix reading &ge; 2<sup>29</sup> pixels per call `--without-performance`
* Fix some `unclosed file` ResourceWarnings on Python 3
* Improve object reprs
* Add test suite
* examples: Drop support for Internet Explorer &lt; 9

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
