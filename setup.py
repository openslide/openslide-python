from distutils.core import setup
import os

# Load version string
_verfile = os.path.join(os.path.dirname(__file__), 'openslide', '_version.py')
with open(_verfile) as _fh:
    exec(_fh.read())

setup(
    name = 'openslide-python',
    version = __version__,
    packages = [
        'openslide',
    ],
    maintainer = 'OpenSlide project',
    maintainer_email = 'openslide-users@lists.andrew.cmu.edu',
    description = 'Python bindings for OpenSlide library',
    license = 'GNU Lesser General Public License, version 2.1',
    keywords = 'openslide whole-slide image library',
    url = 'http://openslide.org/',
)
