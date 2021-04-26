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
 
class Row(object):
    sw = None
    sh = None

    create_tap = None
    tap_distance = None

    create_fill = None

    # Assumption: A fill of size 1 is always available.
    # If not, there WILL be an out of bounds error.
    supported_fill_sizes = None

    def __init__(self, ordinal, row_obj):
        self.ordinal = ordinal
        self.obj = row_obj

        self.origin = self.obj.getOrigin()
        [self.x, self.y] = self.obj.getOrigin()
        self.xmax = self.obj.getBBox().xMax()

        self.ymax = self.obj.getBBox().yMax()
        self.orientation = self.obj.getOrient()

        self.cell_counter = 0
        self.tap_counter = 0
        self.fill_counter = 0
        self.since_last_tap = 0 if self.ordinal % 2 == 0 else Row.tap_distance

    def tap(self, width=0):
        location = self.x

        if self.since_last_tap + width > Row.tap_distance:
            self.place(Row.create_tap("tap_%i_%i" % (self.ordinal, self.tap_counter)), ignore_tap=True)
            self.tap_counter += 1
            self.since_last_tap = 0
        else:
            self.since_last_tap += width

    def place(self, instance, ignore_tap=False):
        width = instance.getMaster().getWidth()
        if not ignore_tap:
            self.tap(width)

        instance.setOrient(self.orientation)
        instance.setLocation(self.x, self.y)
        instance.setPlacementStatus("PLACED")

        self.x += width
        self.cell_counter += 1

    @staticmethod
    def from_odb(rows, regular_site, create_tap, max_tap_distance, create_fill, supported_fill_sizes):
        Row.create_tap = create_tap
        Row.sw, Row.sh = (regular_site.getWidth(), regular_site.getHeight())
        Row.tap_distance = max_tap_distance

        Row.create_fill = create_fill
        Row.supported_fill_sizes = sorted(supported_fill_sizes, reverse=True)

        returnable = []
        for i, row in enumerate(rows):
            returnable.append(Row(i, row))
        return returnable

    @staticmethod
    def fill_rows(rows, from_index, to_index): # [from_index,to_index)
        """
        -- Before this function --

        [A][B][C][D]
        [C][S]
        [F][X][N]
        [V]

        -- After this function --

        [A][B][C][D]
        [C][S][ F  ]
        [F][X][N][F]
        [V][ F  ][F]

        Technology's amazing, innit?

        """
        def pack(size, fill_sizes):
            fills = []
            current = size
            tracker = 0

            while current > 0:
                current_fill = fill_sizes[tracker]
                while current >= current_fill:
                    fills.append(current_fill)
                    current -= current_fill
                tracker += 1

            return fills

        max_sw = -1
        for i in range(from_index, to_index):
            r = rows[i]
            width = r.x
            width_sites = int(width / Row.sw)
            max_sw = max(max_sw, width_sites)

        for i in range(from_index, to_index):
            r = rows[i]
            width = r.x
            width_sites = int(width / Row.sw)

            empty = max_sw - width_sites

            remaining = empty

            fills = pack(empty, Row.supported_fill_sizes)

            for fill in fills:
                fill_cell = Row.create_fill("fill_%i_%i" % (i, r.fill_counter), fill)
                r.place(fill_cell, ignore_tap=True)
                r.fill_counter += 1
