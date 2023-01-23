# -*- coding: utf8 -*-
# Copyright ©2020-2022 The American University in Cairo
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

from .row import Row
from .util import d2a
from .placeable import Placeable

from odb import dbInst as Instance

from typing import List

P = Placeable
S = Placeable.Sieve


class Mux(Placeable):
    """
    Constraint: The number of selection buffers is necessarily == the number of bytes.
    """

    def __init__(self, instances: List[Instance]):
        self.sieve(
            instances,
            [
                S(variable="sel_diodes", groups=["line"]),
                S(variable="selbufs", groups=["byte", "line"], group_rx_order=[2, 1]),
                S(variable="muxes", groups=["byte", "bit"]),
                S(variable="input_diodes", groups=["byte", "input", "bit"]),
            ],
        )
        self.dicts_to_lists()

    def place(self, row_list: List[Row], start_row: int = 0):
        current_row = start_row
        r = row_list[current_row]

        for line in self.sel_diodes:
            r.place(line)

        byte = len(self.muxes)
        for i in range(byte):
            for selbuf in self.selbufs[i]:
                r.place(selbuf)
            for mux in self.muxes[i]:
                r.place(mux)

        current_row += 1

        r = row_list[current_row]

        for i in range(byte):
            for input in self.input_diodes[i]:
                for diode in input:
                    r.place(diode)

        current_row += 1

        return current_row


class Decoder3x8(Placeable):
    def __init__(self, instances: List[Instance]):
        self.sieve(
            instances,
            [
                S(variable="enbuf"),
                S(variable="and_gates", groups=["gate"]),
                S(variable="abufs", groups=["address_bit"]),
                S(variable="invs", groups=["gate"]),
            ],
        )
        self.dicts_to_lists()

    def place(self, row_list: List[Row], start_row: int = 0):
        """
        By placing this decoder, you agree that rows[start_row:start_row+7]
        are at the sole mercy of this function.
        """

        ands_placeable = self.and_gates
        buffers_placeable = [*self.abufs, self.enbuf, None, None, None, None]
        invs_placeable = self.invs

        for i in range(8):
            r = row_list[start_row + i]
            r.place(ands_placeable[i])
            buf = buffers_placeable[i]
            if i<4: 
                inv = invs_placeable[i]

                if inv is not None:
                    r.place(inv)
            if buf is not None:
                r.place(buf)

        return start_row + 8


class Decoder2x4(Placeable):
    def __init__(self, instances):
        self.sieve(instances, [S(variable="and_gates", groups=["address_bit"])])
        self.dicts_to_lists()

    def place(self, row_list, start_row=0):
        for i in range(
            4
        ):  # range is 4 because 2x4 has 4 AND gates put on on top of each other
            r = row_list[start_row + i]
            r.place(self.and_gates[i])

        return start_row + 4


class Decoder5x32(Placeable):
    def __init__(self, instances):
        raw_d2x4 = []

        def process_d2x4_element(instance):
            raw_d2x4.append(instance)

        raw_d3x8 = {}

        def process_d3x8_element(instance, decoder):
            raw_d3x8[decoder] = raw_d3x8.get(decoder) or []
            raw_d3x8[decoder].append(instance)

        self.enbuf = None
        self.sieve(
            instances,
            [
                S(variable="tie"),
                S(variable="decoder2x4", custom_behavior=process_d2x4_element),
                S(
                    variable="decoders3x8",
                    groups=["decoder"],
                    custom_behavior=process_d3x8_element,
                ),
            ],
        )

        self.dicts_to_lists()

        self.decoders3x8 = d2a({k: Decoder3x8(v) for k, v in raw_d3x8.items()})
        self.decoder2x4 = Decoder2x4(raw_d2x4)

    def place(self, row_list, start_row=0, decoder2x4_start_row=0, flip=False):
        r = row_list[start_row]
        r.place(self.tie)

        if flip:
            self.decoder2x4.place(row_list, decoder2x4_start_row)
            for idx in range(len(self.decoders3x8)):
                self.decoders3x8[idx].place(row_list, idx * 8)
            # Row.fill_rows(row_list, start_row, current_row)

        else:
            for idx in range(len(self.decoders3x8)):
                self.decoders3x8[idx].place(row_list, idx * 8)

            self.decoder2x4.place(row_list, decoder2x4_start_row)
            # Row.fill_rows(row_list, start_row, current_row)
        return start_row + 32  # 5x32 has 4 3x8 on top of each other and each is 8 rows
