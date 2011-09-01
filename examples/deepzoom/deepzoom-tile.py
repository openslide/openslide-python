#!/bin/env python
#
# deepzoom-tile - Convert whole-slide images to Deep Zoom format
#
# Copyright (c) 2010-2011 Carnegie Mellon University
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

"""An example program to generate a Deep Zoom directory tree from a slide."""

from multiprocessing import Process, JoinableQueue
from openslide import open_slide
from openslide.deepzoom import DeepZoomGenerator
from optparse import OptionParser
import os
import sys

class TileWorker(Process):
    def __init__(self, queue, slide, tile_size, overlap):
        Process.__init__(self, name='TileWorker')
        self._queue = queue
        self._slide = slide
        self._tile_size = tile_size
        self._overlap = overlap

    def run(self):
        dz = DeepZoomGenerator(open_slide(self._slide), self._tile_size,
                    self._overlap)
        while True:
            data = self._queue.get()
            if data is None:
                self._queue.task_done()
                break
            level, address, outfile = data
            tile = dz.get_tile(level, address)
            tile.save(outfile, optimize=True, quality=90)
            self._queue.task_done()


class DeepZoomStaticTiler(object):
    def __init__(self, slide, basename, format, tile_size, overlap, workers):
        self._basename = basename
        self._format = format
        self._processed = 0
        self._queue = JoinableQueue(2 * workers)
        self._workers = workers
        for _i in range(workers):
            TileWorker(self._queue, slide, tile_size, overlap).start()
        self._dz = DeepZoomGenerator(open_slide(slide), tile_size, overlap)

    def run(self):
        self._write_tiles()
        self._write_dzi()

    def _write_tiles(self):
        for level in xrange(self._dz.level_count):
            tiledir = os.path.join("%s_files" % self._basename, str(level))
            if not os.path.exists(tiledir):
                os.makedirs(tiledir)
            cols, rows = self._dz.level_tiles[level]
            for row in xrange(rows):
                for col in xrange(cols):
                    tilename = os.path.join(tiledir, '%d_%d.%s' % (
                                    col, row, self._format))
                    if not os.path.exists(tilename):
                        self._queue.put((level, (col, row), tilename))
                    self._tile_done()
        for _i in range(self._workers):
            self._queue.put(None)
        self._queue.join()

    def _tile_done(self):
        self._processed += 1
        count, total = self._processed, self._dz.tile_count
        if count % 100 == 0 or count == total:
            print >> sys.stderr, "Wrote %d/%d tiles\r" % (count, total),
            if count == total:
                print

    def _write_dzi(self):
        with open('%s.dzi' % self._basename, 'w') as fh:
            fh.write(self._dz.get_dzi(self._format))


if __name__ == '__main__':
    parser = OptionParser(usage='Usage: %prog [options] <slide>')
    parser.add_option('-e', '--overlap', metavar='PIXELS', dest='overlap',
                type='int', default=1,
                help='overlap of adjacent tiles [1]')
    parser.add_option('-f', '--format', metavar='{jpeg|png}', dest='format',
                default='jpeg',
                help='image format for tiles [jpeg]')
    parser.add_option('-j', '--jobs', metavar='COUNT', dest='workers',
                type='int', default=4,
                help='number of worker processes to start [4]')
    parser.add_option('-o', '--output', metavar='NAME', dest='basename',
                help='base name of output file')
    parser.add_option('-s', '--size', metavar='PIXELS', dest='tile_size',
                type='int', default=256,
                help='tile size [256]')

    (opts, args) = parser.parse_args()
    try:
        slidefile = args[0]
    except IndexError:
        parser.error('Missing slide argument')
    if opts.basename is None:
        opts.basename = os.path.splitext(os.path.basename(slidefile))[0]

    DeepZoomStaticTiler(slidefile, opts.basename, opts.format,
                opts.tile_size, opts.overlap, opts.workers).run()
