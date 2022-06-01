from distutils.command.build_ext import build_ext
from distutils.core import Extension

# C Extensions
extensions = [
    Extension('openslide._convert', ['openslide/_convert.c']),
]


def build(setup_kwargs):
    """
    This function is mandatory in order to build the extensions.
    """
    setup_kwargs.update(
        {'ext_modules': extensions, 'cmdclass': {'build_ext': build_ext}}
    )
