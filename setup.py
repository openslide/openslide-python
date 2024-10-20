import sys

from setuptools import Extension, setup

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
    package_data={
        'openslide': ['py.typed'],
    },
)
