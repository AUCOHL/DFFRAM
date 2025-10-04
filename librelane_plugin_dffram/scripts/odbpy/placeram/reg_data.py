# -*- coding: utf8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright ©2020-2022, The American University in Cairo

from .row import Row
from .util import d2a
from .placeable import Placeable
from .common_data import Decoder5x32

from odb import dbInst as Instance
from typing import Dict, List

P = Placeable
S = Placeable.Sieve


class Bit(Placeable):
    def __init__(self, instances: List[Instance]):
        self.sieve(
            instances, [S(variable="store"), S(variable="obufs", groups=["port"])]
        )

        self.dicts_to_lists()

    def place(self, row_list: List[Row], start_row: int = 0):
        r = row_list[start_row]

        r.place(self.store)
        for obuf in self.obufs:
            r.place(obuf)

        return start_row


class RFWord(Placeable):
    def __init__(self, instances):
        self.raw_bits: Dict[int, List[Instance]] = {}

        def process_bit(instance, bit):
            self.raw_bits[bit] = self.raw_bits.get(bit) or []
            self.raw_bits[bit].append(instance)

        self.sieve(
            instances,
            [
                S(variable="ffs", groups=["bit"], custom_behavior=process_bit),
                S(variable="clkgateand"),
                S(variable="clkgates", groups=["ports"]),
                S(variable="obufs", groups=["ports", "bit"], group_rx_order=[2, 1]),
                S(variable="selinv", groups=["ports", "bit"], group_rx_order=[2, 1]),
                S(variable="invs", groups=["ports", "address_bit"]),
            ],
        )

        self.dicts_to_lists()

    def place(self, row_list, start_row=0):
        raise Exception(
            "Register file words cannot be placed solo as the bits have to be in lockstep."
        )

    def word_width(self):
        return len(self.raw_bits)

    def word_count(self):
        return 1


class DFFRF(Placeable):  # 32 words
    def __init__(self, instances):
        raw_words: Dict[int, List[Instance]] = {}

        def process_word(instance, word):
            raw_words[word] = raw_words.get(word) or []
            raw_words[word].append(instance)

        raw_decoders: Dict[int, List[Instance]] = {}

        def process_decoder(instance, decoder):
            raw_decoders[decoder] = raw_decoders.get(decoder) or []
            raw_decoders[decoder].append(instance)

        self.sieve(
            instances,
            [
                S(
                    variable="decoders",
                    groups=["decoder"],
                    custom_behavior=process_decoder,
                ),
                S(variable="words", groups=["word"], custom_behavior=process_word),
                S(variable="rfw0_ties", groups=["nibble"]),
                S(variable="rfw0_invs1", groups=["byte"]),
                S(variable="rfw0_invs2", groups=["byte"]),
                S(variable="rfw0_obufs1", groups=["bit"]),
                S(variable="rfw0_selinv1", groups=["bit"]),
                S(variable="rfw0_obufs2", groups=["bit"]),
                S(variable="rfw0_selinv2", groups=["bit"]),
                S(variable="tiezero"),
            ],
        )

        self.dicts_to_lists()

        self.words: List[RFWord] = d2a({k: RFWord(v) for k, v in raw_words.items()})
        self.decoders5x32: List[Decoder5x32] = d2a(
            {k: Decoder5x32(v) for k, v in raw_decoders.items()}
        )

    def place(self, rows, start_row: int = 0):
        #    |      5x32 Decoder Placement           |  |
        #    |                                       |  |
        #    |                                       |  |
        #    V                                       V  V
        # {  _ ====================================  ____   }
        # 32 _ ====================================  ____  32
        # { D2 ====================================  D0 D1  }
        word_rows = 32 * 2 - 2 + 1  # word 0 only needs one row
        word_width = self.words[0].word_width()

        # D2 placement
        self.decoders5x32[2].place(rows, start_row, (32 - 4) // 2, flip=True)

        Row.fill_rows(rows, start_row, start_row + word_rows - 1)

        # This loop places each column of bits on the same general X-position
        # to make routing easier.

        for bit in range(0, word_width):
            byte = bit // 8
            nibble = bit // 4
            current_row = start_row

            row = rows[current_row]

            if bit % 8 == 0:
                row.place(self.rfw0_invs1[byte])
                row.place(self.rfw0_invs2[byte])

            if bit % 4 == 0:
                row.place(self.rfw0_ties[nibble])

            if bit < len(self.rfw0_selinv1):
                row.place(self.rfw0_selinv1[bit])

            row.place(self.rfw0_obufs1[bit])

            if bit < len(self.rfw0_selinv2):
                row.place(self.rfw0_selinv2[bit])
            row.place(self.rfw0_obufs2[bit])

            current_row += 1

            for word in self.words:
                row0 = rows[current_row]
                row1 = rows[current_row + 1]

                if bit % 8 == 0:  # Per Byte
                    for inverter_set in word.invs:
                        row0.place(inverter_set[bit // 8])
                    row0.place(word.clkgates[bit // 8])

                if bit == (word_width // 2):
                    row0.place(word.clkgateand)

                row0.place(word.ffs[bit])

                for selinv in word.selinv:
                    row1.place(selinv[bit])

                for obufs in word.obufs:
                    row1.place(obufs[bit])

                current_row += 2

            if self.tiezero is not None:
                row.place(self.tiezero)
            Row.fill_rows(rows, start_row, current_row)

        # D0 placement
        self.decoders5x32[0].place(rows, start_row, 4)
        # D1 placement
        self.decoders5x32[1].place(rows, start_row, 20)

        Row.fill_rows(rows, start_row, current_row)
        return current_row

    def word_count(self):
        return 32
