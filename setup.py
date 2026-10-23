import sys
import sysconfig

from setuptools import Extension, setup
from setuptools import __version__ as _setuptools_ver

# Use the free-threaded Stable ABI (abi3t) only on free-threaded Python
# 3.15+ with setuptools 84.2+; Python supports building abi3t from
# GIL-enabled interpreters but setuptools doesn't yet.  Use the
# non-free-threaded Stable API (abi3) with GIL enabled, and
# release-specific wheels in all other cases.
_freethread = sysconfig.get_config_var('Py_GIL_DISABLED')
_abi3t = (
    sys.version_info >= (3, 15)
    and _freethread
    and tuple(int(c) for c in _setuptools_ver.split('.')) >= (84, 2)
)
_abi3 = not _freethread

setup(
    ext_modules=[
        Extension(
            'openslide._convert',
            ['openslide/_convert.c'],
            # hide symbols that aren't in the Limited API
            define_macros=[('Py_TARGET_ABI3T', '0x030f0000')]
            if _abi3t
            else [('Py_LIMITED_API', '0x030b0000')]
            if _abi3
            else [],
            # tag extension module for Stable ABI
            py_limited_api=_abi3 or _abi3t,
        ),
    ],
    options={
        # tag wheel for Stable ABI
        'bdist_wheel': {'py_limited_api': 'cp315'}
        if _abi3t
        else {'py_limited_api': 'cp311'}
        if _abi3
        else {},
    },
)
