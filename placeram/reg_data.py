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

from .row import Row
from .util import d2a
from .placeable import Placeable
from .common_data import *

from opendbpy import dbInst
from typing import Dict, List
Instance = dbInst

P = Placeable
S = Placeable.Sieve

class RFWord(Placeable):
    def __init__(self, instances):
        self.sieve(instances, [
            S(variable="clkgateand"),
            S(variable="ffs", groups=["bit"]),
            S(variable="clkgates", groups=["ports"]),
            S(variable="obufs", groups=["ports", "bit"], group_rx_order=[2, 1]),
            S(variable="invs", groups=["ports", "address_bit"])
        ])
        
        self.dicts_to_lists()

    def place(self, row_list, start_row=0):
        r = row_list[start_row]
        word_width = 32
        for i in range(word_width): # 32
            # TODO: Use middle placement
            # to make the clkgateand an equal distance from all
            # gates that need its output

            if i % 8 == 0: # range(4) every 8 place an inv
                for invs in self.invs:
                    r.place(invs[i//8])
            if i == (word_width // 2): # 16 range(1)
                r.place(self.clkgateand)
            if i % 8 == 0: # range(4) every 8 place a clk gate
                r.place(self.clkgates[i//8])

            r.place(self.ffs[i])
            for obufs in self.obufs:
                r.place(obufs[i])

        return start_row + 1

    def word_count(self):
        return 1


class DFFRF(Placeable): # 32 words
    def __init__(self, instances):
        raw_words: Dict[int, List[Instance]] = {}
        def process_word(instance, word):
            raw_words[word] = raw_words.get(word) or []
            raw_words[word].append(instance)

        raw_decoders: Dict[int, List[Instance]] = {}
        def process_decoder(instance, decoder):
            raw_decoders[decoder] = raw_decoders.get(decoder) or []
            raw_decoders[decoder].append(instance)

        self.sieve(instances, [            
            S(variable="decoders", groups=["decoder"], custom_behavior=process_decoder),
            S(variable="words", groups=["word"], custom_behavior=process_word),
            S(variable="rfw0_ties", groups=["bit"]),
            S(variable="rfw0_invs1", groups=["bit"]),
            S(variable="rfw0_invs2", groups=["bit"]),
            S(variable="rfw0_obufs1", groups=["bit"]),
            S(variable="rfw0_obufs2", groups=["bit"]),
        ])

        self.dicts_to_lists()

        self.words = d2a({k: RFWord(v) for k, v in raw_words.items()})
        self.decoders5x32 = d2a({k: Decoder5x32(v) for k, v in raw_decoders.items()})

    def place(self, row_list, start_row=0):
        #    |      5x32 decoders placement          |  |
        #    |                                       |  |
        #    |                                       |  |
        #    V                                       V  V
        #  { _ ====================================  ____   }
        # 32 _ ====================================  ____  32
        #  { D2 ==================================== D0 D1  }

        # D2 placement
        def width_rfw0():
            tot_width = 0

            for inverter in [*self.rfw0_invs1, *self.rfw0_invs2]:
                tot_width += inverter.getMaster().getWidth()
            for atie in self.rfw0_ties:
                tot_width += atie.getMaster().getWidth()
            for anobuf in [*self.rfw0_obufs1,*self.rfw0_obufs2] :
                tot_width += anobuf.getMaster().getWidth()

            return tot_width

        def rfw0_placement_start(row_list, start_row,
                                x_start, x_current,
                                x_end):
            design_width = x_end - x_start
            return x_current + ((design_width - width_rfw0()) // 2)

        def place_rfw0(row, start_loc):
            # RFWORD0 placement
            # Should center this row
            # get width of the design and then put equal
            # distance around this row both on left and right

            start_row = 0
            row.x = start_loc

            for i in range(32):
                if i % 8 == 0: # range(4)
                    row.place(self.rfw0_invs1[i//8])
                    row.place(self.rfw0_invs2[i//8])
                if i % 4 == 0: # range(8)
                    row.place(self.rfw0_ties[i//4])
                row.place(self.rfw0_obufs1[i])
                row.place(self.rfw0_obufs2[i])
            return row.x


        self.decoders5x32[2].place(row_list, start_row, (32-4)//2, flip=True)
        row0_empty_space_1_start = row_list[start_row].x
        words_start_x = row0_empty_space_1_start

        current_row = start_row + 1
        for aword in self.words:
            aword.place(row_list, current_row)
            current_row += 1

        highest_row = current_row
        words_end_x = row_list[1].x
        row0_empty_space_2_end = words_end_x

        # D0 placement
        self.decoders5x32[0].place(row_list, start_row, 4)
        # D1 placement
        self.decoders5x32[1].place(row_list, start_row, 20)

        row0_empty_space_1_end = rfw0_placement_start(row_list, 0,
                                    words_start_x,
                                    row_list[0].x,
                                    words_end_x)
        Row.fill_row(row_list,
                0,
                row0_empty_space_1_start,
                row0_empty_space_1_end)

        row0 = row_list[0]
        rfw0_placement_end = place_rfw0(row0,
                                        row0_empty_space_1_end)
        row0_empty_space_2_start = rfw0_placement_end


        Row.fill_row(row_list,
                0,
                row0_empty_space_2_start,
                row0_empty_space_2_end)

        # Fill all empty spaces on edges
        Row.fill_rows(row_list, start_row, highest_row)
        return highest_row

    def word_count(self):
        return 32
