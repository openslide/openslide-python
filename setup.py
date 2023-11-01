from setuptools import Extension, setup

setup(
    ext_modules=[
        Extension('openslide._convert', ['openslide/_convert.c']),
    ],
)
