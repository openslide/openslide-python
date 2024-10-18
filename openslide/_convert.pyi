#
# openslide-python - Python bindings for the OpenSlide library
#
# Copyright (c) 2024 Benjamin Gilbert
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

from typing import Protocol

class _Buffer(Protocol):
    # Python 3.12+ has collections.abc.Buffer
    def __buffer__(self, flags: int) -> memoryview: ...

def argb2rgba(buf: _Buffer) -> None: ...
