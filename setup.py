from pathlib import Path
import sys

from setuptools import Extension, setup

# Load version string
with open(Path(__file__).parent / 'openslide/_version.py') as _fh:
    exec(_fh.read())  # instantiates __version__

# use the Limited API on Python 3.11+; build release-specific wheels on
# older Python
_abi3 = sys.version_info >= (3, 11)

setup(
    ext_modules=[
        Extension(
            'openslide._convert',
            ['openslide/_convert.c'],
            # hide symbols that aren't in the Limited API
            define_macros=[('Py_LIMITED_API', '0x030b0000')] if _abi3 else [],
            # tag extension module for Limited API
            py_limited_api=_abi3,
        ),
    ],
    options={
        # tag wheel for Limited API
        'bdist_wheel': {'py_limited_api': 'cp311'} if _abi3 else {},
    },
    #
    # setuptools < 61 compatibility for distro packages building from source
    name='openslide-python',
    version=__version__,  # type: ignore[name-defined]  # noqa: F821
    install_requires=[
        'Pillow',
    ],
    packages=[
        'openslide',
    ],
    package_data={
        'openslide': ['py.typed', '*.pyi'],
    },
    zip_safe=False,
)
