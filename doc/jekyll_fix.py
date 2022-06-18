#
# openslide-python - Python bindings for the OpenSlide library
#
# Copyright (c) 2014 Carnegie Mellon University
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of version 2.1 of the GNU Lesser General Public License
# as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

# Sphinx hardcodes that certain output paths have names starting with
# an underscore.
# Jekyll hardcodes that filenames starting with an underscore are not
# deployed to the website.
# Rename Sphinx output paths to drop the underscore.

import os

from sphinx.util import logging
from sphinx.util.console import bold

DIRS = {
    '_static': 'static',
    '_sources': 'sources',
}
FILES = {
    # Added in Sphinx 5.0.0, scheduled to be removed in Sphinx 6
    'static/_sphinx_javascript_frameworks_compat.js': 'static/sphinx_javascript_frameworks_compat.js',  # noqa: E501
}
REWRITE_EXTENSIONS = {'.html', '.js'}


def remove_path_underscores(app, exception):
    if exception:
        return
    # Get logger
    logger = logging.getLogger(__name__)
    logger.info(bold('fixing pathnames... '), nonl=True)
    # Rewrite references in HTML/JS files
    for dirpath, _, filenames in os.walk(app.outdir):
        for filename in filenames:
            _, ext = os.path.splitext(filename)
            if ext in REWRITE_EXTENSIONS:
                path = os.path.join(dirpath, filename)
                with open(path, encoding='utf-8') as fh:
                    contents = fh.read()
                for old, new in DIRS.items():
                    contents = contents.replace(old + '/', new + '/')
                for old, new in FILES.items():
                    contents = contents.replace(old, new)
                with open(path, 'w', encoding='utf-8') as fh:
                    fh.write(contents)
    # Move directory contents
    for old, new in DIRS.items():
        olddir = os.path.join(app.outdir, old)
        newdir = os.path.join(app.outdir, new)
        if not os.path.exists(newdir):
            os.mkdir(newdir)
        if os.path.isdir(olddir):
            for filename in os.listdir(olddir):
                oldfile = os.path.join(olddir, filename)
                newfile = os.path.join(newdir, filename)
                os.rename(oldfile, newfile)
            os.rmdir(olddir)
    # Move files
    for old, new in FILES.items():
        oldfile = os.path.join(app.outdir, old)
        newfile = os.path.join(app.outdir, new)
        if os.path.isfile(oldfile):
            os.rename(oldfile, newfile)
    logger.info('done')


def setup(app):
    app.connect('build-finished', remove_path_underscores)
