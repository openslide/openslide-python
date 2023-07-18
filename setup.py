import os

from setuptools import Extension, setup

# Load version string
_verfile = os.path.join(os.path.dirname(__file__), 'openslide', '_version.py')
with open(_verfile) as _fh:
    exec(_fh.read())  # instantiates __version__

with open('README.md') as _fh:
    _long_description = _fh.read()

setup(
    name='openslide-python',
    version=__version__,  # noqa: F821  undefined-name __version__
    packages=[
        'openslide',
    ],
    ext_modules=[
        Extension('openslide._convert', ['openslide/_convert.c']),
    ],
    test_suite='tests',
    maintainer='OpenSlide project',
    maintainer_email='openslide-users@lists.andrew.cmu.edu',
    description='Python interface to OpenSlide',
    long_description=_long_description,
    long_description_content_type='text/markdown',
    license='GNU Lesser General Public License, version 2.1',
    keywords='openslide whole-slide image virtual slide library',
    url='https://openslide.org/',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Healthcare Industry',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
    ],
    python_requires='>=3.8',
    install_requires=[
        'Pillow',
    ],
    zip_safe=True,
)
