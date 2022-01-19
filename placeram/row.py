# -*- coding: utf8 -*-
# Copyright ©2020-2021 The American University in Cairo and the Cloud V Project.
#
# This file is part of the DFFRAM Memory Compiler.
# See https://github.com/Cloud-V/DFFRAM for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from odb import dbRow, dbInst, dbSite
from typing import List, Callable

import re


class Row(object):
    sw: float = None
    sh: float = None

    tap_rx: str = None
    tap_distance: float = None

    # Assumption: A fill of size 1 is always available.
    # If not, there WILL be an out of bounds error.
    # The fill of size 1 is also the tap cell.
    create_fill: Callable[[str, int], dbInst] = None
    supported_fill_sizes: List[int] = None

    def __init__(self, ordinal, row_obj):
        self.ordinal: int = ordinal
        self.obj: dbRow = row_obj

        self.origin: List[float] = self.obj.getOrigin()
        self.x: float = self.origin[0]
        self.y: float = self.origin[1]

        self.xmin: float = self.obj.getBBox().xMin()
        self.xmax: float = self.obj.getBBox().xMax()

        self.ymin: float = self.obj.getBBox().yMin()
        self.ymax: float = self.obj.getBBox().yMax()

        self.orientation = self.obj.getOrient()

        self.cell_counter: int = 0
        self.tap_counter: int = 0
        self.fill_counter: int = 0
        self.since_last_tap: float = 0 if self.ordinal % 2 == 0 else Row.tap_distance

    @property
    def width(self):
        return self.x - self.xmin

    def tap(self, width: float = 0):
        if self.since_last_tap + width > Row.tap_distance:
            self.place(
                Row.create_fill("tap_%i_%i" % (self.ordinal, self.tap_counter), 1),
                ignore_tap=True,
            )
            self.tap_counter += 1

    def place(self, instance: dbInst, ignore_tap: bool = False):
        width = instance.getMaster().getWidth()
        if not ignore_tap:
            self.tap(width)

        instance.setOrient(self.orientation)
        instance.setLocation(self.x, self.y)
        instance.setPlacementStatus("PLACED")

        if re.match(Row.tap_rx, instance.getMaster().getName()):
            self.since_last_tap = 0
        else:
            self.since_last_tap += width
        self.x += width
        self.cell_counter += 1

    @staticmethod
    def from_odb(
        rows: List[dbRow],
        regular_site: dbSite,
        max_tap_distance: float,
        create_fill: Callable[[str, int], dbInst],
        supported_fill_sizes: List[int],
        tap_cell_rx: str,
    ):
        Row.sw, Row.sh = (regular_site.getWidth(), regular_site.getHeight())
        Row.tap_distance = max_tap_distance

        Row.create_fill = create_fill
        Row.supported_fill_sizes = sorted(supported_fill_sizes, reverse=True)
        Row.tap_rx = tap_cell_rx

        returnable = []
        for i, row in enumerate(rows):
            returnable.append(Row(i, row))
        return returnable

    @staticmethod
    def fill_rows(rows: List["Row"], from_index: int, to_index: int):
        """
        from inclusive; to exclusive
        Fills from the last location that has a cell.

        -- Before this function --

        [A][B][C][D]
        [C][S]
        [F][X][N]
        [V]   [K]

        -- After this function --

        [A][B][C][D]
        [C][S][ F  ]
        [F][X][N][F]
        [V]   [K][F]

        """

        def pack(size, fill_sizes):
            fills = []
            current = size
            tracker = 0

            since_last_tap = 0
            if current > 1:
                # Always start with a tap.
                fills.append(1)
                current -= 1

            while current > 0:
                current_fill = fill_sizes[tracker]
                current_width = current_fill * Row.sw
                while current >= current_fill:
                    if since_last_tap + current_width > Row.tap_distance:
                        fills.append(1)
                        since_last_tap = 0
                        current -= 1
                    else:
                        fills.append(current_fill)
                        since_last_tap += current_width
                        current -= current_fill
                tracker += 1

            return fills

        max_sw = -1
        for row_idx in range(from_index, to_index):
            r = rows[row_idx]
            width = r.x
            width_sites = int(width / Row.sw)
            max_sw = max(max_sw, width_sites)

        for row_idx in range(from_index, to_index):
            r = rows[row_idx]
            width = r.x
            width_sites = int(width / Row.sw)

            empty = max_sw - width_sites

            fills = pack(empty, Row.supported_fill_sizes)
            # print(f"{from_index}->{to_index}::{row_idx}: {fills}")
            for fill in fills:
                fill_cell = Row.create_fill(
                    "fill_%i_%i" % (row_idx, r.fill_counter), fill
                )
                r.place(fill_cell, ignore_tap=True)
                r.fill_counter += 1
