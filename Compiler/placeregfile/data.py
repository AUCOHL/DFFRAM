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

from .util import eprint, grouped_sorted
from .row import Row

from opendbpy import dbInst
Instance = dbInst

import re
import sys
import math
from functools import partial
# --
def str_instance(instance):
    return "[I<%s> '%s']" % (instance.getMaster().getName(), instance.getName())

class Placeable(object):
    experimental_mode = False

    def place(self, row_list, current_row=0):
        raise Exception("Method unimplemented.")

    def represent(self, tab_level=-1, file=sys.stderr):
        raise Exception("Method unimplemented.")

    def word_count(self):
        raise Exception("Method unimplemented.")

    @staticmethod
    def represent_instance(name, instance, tab_level, file=sys.stderr):
        if name != "":
            name += " "
        print("%s%s%s" % ("".join(["  "] * tab_level), name, str_instance(instance)), file=file)

    ri = represent_instance

    @staticmethod
    def represent_array(name, array, tab_level, file=sys.stderr, header=None):
        if name != "":
            print("%s%s" % ("".join(["  "] * tab_level), name), file=file)
        tab_level += 1
        for i, instance in enumerate(array):
            if header is not None:
                print("%s%s %i" % ("".join(["  "] * tab_level), header, i), file=file)

            if isinstance(instance, list):
                Placeable.represent_array("", instance, tab_level, file)
            elif isinstance(instance, Placeable):
                instance.represent(tab_level, file)
            else:
                Placeable.represent_instance("", instance, tab_level, file)

        tab_level -= 1

    ra = represent_array

class DataError(Exception):
    pass
# --

P = Placeable

# REMOVED
# class Bit(Placeable):
#     def __init__(self, instances):
#         self.store = None
#         self.obuf1 = None
#         self.obuf2 = None

#         latch = r"\bLATCH\b"
#         ff = r"\bFF\b"
#         obuf1 = r"\bOBUF1\b"
#         obuf2 = r"\bOBUF2\b"

#         for instance in instances:
#             n = instance.getName()

#             if 1:
#                 pass
#             # TODO(ahmednofal): might be useful so left it
#             elif latch_match := re.search(latch, n):
#                 self.store = instance
#             else:
#                 raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

#     def place(self, row_list, start_row=0):
#         r = row_list[start_row]

#         r.place(self.obuf1)
#         r.place(self.store)
#         r.place(self.obuf2)

#         return start_row

class Word(Placeable):
    def __init__(self, instances):
        self.clkgateand = None

        clkgate = r"CG\\\[(\d+)\\\]"
        clkgateand = r"CGAND" # placed at its pin at the right
        inv1 = r"INV1\\\[(\d+)\\\]"
        inv2 = r"INV2\\\[(\d+)\\\]"
        bit_ff = r"BIT\\\[(\d+)\\\]\.FF"
        bit_obuf1 = r"BIT\\\[(\d+)\\\]\.OBUF1"
        bit_obuf2 = r"BIT\\\[(\d+)\\\]\.OBUF2"

        raw_clkgates = {}
        raw_ffs = {}
        raw_obufs1 = {}
        raw_obufs2 = {}
        raw_invs1 = {}
        raw_invs2 = {}

        for instance in instances:
            n = instance.getName()

            if clkgate_match := re.search(clkgate, n):
                i = int(clkgate_match[1])
                raw_clkgates[i] = instance

            elif inv1_match := re.search(inv1, n):
                i = int(inv1_match[1])
                raw_invs1[i] = instance

            elif inv2_match := re.search(inv2, n):
                i = int(inv2_match[1])
                raw_invs2[i] = instance

            elif bit_ff_match := re.search(bit_ff, n):
                i = int(bit_ff_match[1])
                raw_ffs[i] = instance

            elif bit_obuf1_match := re.search(bit_obuf1, n):
                i = int(bit_obuf1_match[1])
                raw_obufs1[i] = instance

            elif bit_obuf2_match := re.search(bit_obuf2, n):
                i = int(bit_obuf2_match[1])
                raw_obufs2[i] = instance

            elif clkgateand_match := re.search(clkgateand, n):
                self.clkgateand = instance

            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.clkgates = grouped_sorted(raw_clkgates)
        self.invs1 = grouped_sorted(raw_invs1)
        self.invs2 = grouped_sorted(raw_invs2)
        self.ffs = grouped_sorted(raw_ffs)
        self.obufs1 = grouped_sorted(raw_obufs1)
        self.obufs2 = grouped_sorted(raw_obufs2)

    def place(self, row_list, start_row=0):
        r = row_list[start_row]
        word_width = 32
        for i in range(word_width): # 32
            # to make the clkgateand an equal distance from all
            # gates that need its output

            if i % 8 == 0: # range(4) every 8 place an inv
                r.place(self.invs1[i//8])
                r.place(self.invs2[i//8])
            if i == (word_width // 2): # 16 range(1)
                r.place(self.clkgateand)
            if i % 8 == 0: # range(4) every 8 place a clk gate
                r.place(self.clkgates[i//8])

            r.place(self.ffs[i])
            r.place(self.obufs1[i])
            r.place(self.obufs2[i])

        return start_row + 1

    def word_count(self):
        return 1


class DFFRF(Placeable): # 32 words
    def __init__(self, instances):

        raw_words = {}
        raw_decoders5x32 = {}

        word = r"\bFILE\\\[(\d+)\\\]\.RFW\b"
        decoder5x32 = r"\bDEC(\d+)\b"

        raw_rfw0_ties = {}
        raw_rfw0_invs1 = {}
        raw_rfw0_invs2 = {}
        raw_rfw0_obufs1 = {}
        raw_rfw0_obufs2 = {}

        rfw0_tie = r"RFW0\.TIE\\\[(\d+)\\\]"
        rfw0_inv1 = r"RFW0\.INV1\\\[(\d+)\\\]"
        rfw0_inv2 = r"RFW0\.INV2\\\[(\d+)\\\]"
        rfw0_obuf1 = r"\bRFW0\.BIT\\\[(\d+)\\\]\.OBUF1\b"
        rfw0_obuf2 = r"\bRFW0\.BIT\\\[(\d+)\\\]\.OBUF2\b"

        for instance in instances:
            n = instance.getName()

            if word_match := re.search(word, n):
                i = int(word_match[1])
                raw_words[i] = raw_words.get(i) or []
                raw_words[i].append(instance)

            elif decoder5x32_match := re.search(decoder5x32, n):
                i = int(decoder5x32_match[1])
                raw_decoders5x32[i] = raw_decoders5x32.get(i) or []
                raw_decoders5x32[i].append(instance)

            elif rfw0_obuf_match1 := re.search(rfw0_obuf1, n):
                bit = int(rfw0_obuf_match1[1])
                raw_rfw0_obufs1[bit] = instance

            elif rfw0_obuf_match2 := re.search(rfw0_obuf2, n):
                bit = int(rfw0_obuf_match2[1])
                raw_rfw0_obufs2[bit] = instance

            elif rfw0_tie_match := re.search(rfw0_tie, n):
                i = int(rfw0_tie_match[1])
                raw_rfw0_ties[i] = instance

            elif rfw0_inv1_match := re.search(rfw0_inv1, n):
                i = int(rfw0_inv1_match[1])
                raw_rfw0_invs1[i] = instance

            elif rfw0_inv2_match := re.search(rfw0_inv2, n):
                i = int(rfw0_inv2_match[1])
                raw_rfw0_invs2[i] = instance

            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.words = grouped_sorted({k: Word(v) for k, v in raw_words.items()})
        self.decoders5x32 = grouped_sorted({k: Decoder5x32(v) for k, v in raw_decoders5x32.items()})

        self.rfw0_ties = grouped_sorted(raw_rfw0_ties)
        self.rfw0_invs1 = grouped_sorted(raw_rfw0_invs1)
        self.rfw0_invs2 = grouped_sorted(raw_rfw0_invs2)
        self.rfw0_obufs1 = grouped_sorted(raw_rfw0_obufs1)
        self.rfw0_obufs2 = grouped_sorted(raw_rfw0_obufs2)

    def place(self, row_list, start_row=0):
        #           5x32 decoders placement          |
        #                                            |
        #                                            |
        #                        D0                  V
        #  {    ====================================    }
        # 32 D2 ==================================== D1 32
        #  {    ====================================    }

        # D2 placement
        current_row = start_row
        # self.decoders5x32[2].place(row_list, current_row)

        thisrow = self.decoders5x32[2].place(row_list, start_row, flip=True)
        r = row_list[start_row]
        # RFWORD0 placement
        for i in range(32):
            if i % 8 == 0: # range(4)
                r.place(self.rfw0_invs1[i//8])
                r.place(self.rfw0_invs2[i//8])
            if i % 4 == 0: # range(8)
                r.place(self.rfw0_ties[i//4])
            r.place(self.rfw0_obufs1[i])
            r.place(self.rfw0_obufs2[i])

        current_row += 1

        for aword in self.words:
            aword.place(row_list, current_row)
            current_row += 1

        highest_row = current_row
        # D0 placement
        current_row = self.decoders5x32[0].place(row_list, start_row)
        # D1 placement
        current_row = self.decoders5x32[1].place(row_list, start_row)
        Row.fill_rows(row_list, start_row, current_row)

        return highest_row

    def word_count(self):
        return 32

class Decoder5x32(Placeable):
    def __init__(self, instances):
        self.enbuf = None


        decoder2x4 = r"DEC(\d+)\.D"
        decoder3x8 = r"DEC(\d+)\.D(\d+)"

        raw_decoders3x8 = {} # multiple decoders so multiple entries ordered by 1st match
        self.decoder2x4 = [] # one decoder so array

        for instance in instances:
            n = instance.getName()

            if decoder3x8_match := re.search(decoder3x8, n):
                i = int(decoder3x8_match[2])
                raw_decoders3x8[i] = raw_decoders3x8.get(i) or []
                raw_decoders3x8[i].append(instance)

            elif decoder2x4_match := re.search(decoder2x4, n):
                # TODO(ahmednofal): check if these instances
                # are not ordered so it might not be
                # the most optimal placement
                self.decoder2x4.append(instance)
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.decoders3x8 = grouped_sorted({k: Decoder3x8(v) for k, v in raw_decoders3x8.items()})
        self.decoder2x4 = Decoder2x4(self.decoder2x4)

    def place(self, row_list, start_row=0, flip=False):
        current_row = start_row

        if flip:
            thisrow = self.decoder2x4.place(row_list, start_row)
            for idx in range(len(self.decoders3x8)):
                self.decoders3x8[idx].place(row_list, idx*8)
            Row.fill_rows(row_list, start_row, thisrow)

        else:
            for idx in range(len(self.decoders3x8)):
                self.decoders3x8[idx].place(row_list, idx*8)

            thisrow = self.decoder2x4.place(row_list, start_row)
            Row.fill_rows(row_list, start_row, thisrow)
        return start_row + 32 # 5x32 has 4 3x8 on top of each other and each is 8 rows

class Decoder3x8(Placeable):
    def __init__(self, instances):
        self.andgates = instances
        if len(instances) < 8:
            for aninstance in instances:
                print(aninstance.getName())

    def place(self, row_list, start_row=0):
        """
        By placing this decoder, you agree that rows[start_row:start_row+7]
        are at the sole mercy of this function.
        """

        for i in range(8): # range is 8 because 3x8 has 8 and gates put on on top of each other
            r = row_list[start_row + i]
            if i < len(self.andgates):
                r.place(self.andgates[i])

        return start_row + 8

class Decoder2x4(Placeable):
    def __init__(self, instances):
        self.andgates = instances

    def place(self, row_list, start_row=0):
        for i in range(4): # range is 8 because 3x8 has 8 and gates put on on top of each other
            r = row_list[start_row + i]
            r.place(self.andgates[i])

        return start_row + 4
