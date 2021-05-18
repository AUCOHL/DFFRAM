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

class Bit(Placeable):
    def __init__(self, instances):
        self.store = None
        self.obuf1 = None
        self.obuf2 = None

        latch = r"\bLATCH\b"
        ff = r"\bFF\b"
        obuf1 = r"\bOBUF1\b"
        obuf2 = r"\bOBUF2\b"

        for instance in instances:
            n = instance.getName()

            if ff_match := re.search(ff, n):
                self.store = instance
            elif obuf1_match := re.search(obuf1, n):
                self.obuf1 = instance
            elif obuf2_match := re.search(obuf2, n):
                self.obuf2 = instance
            # TODO(ahmednofal): might be useful so left it
            elif latch_match := re.search(latch, n):
                self.store = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

    def place(self, row_list, start_row=0):
        r = row_list[start_row]

        r.place(self.obuf1)
        r.place(self.store)
        r.place(self.obuf2)

        return start_row

class Word(Placeable):
    def __init__(self, instances):
        self.clkgateand = None

        clkgate = r"\bCG\\\[(\d+)\\\]\b"
        clkgateand = r"\bCGAND\b" # placed at its pin at the right
        inv1 = r"\bINV1\\\[(\d+)\\\]\b"
        inv2 = r"\bINV2\\\[(\d+)\\\]\b"
        bit = r"\bBIT\\\[(\d+)\\\]\b"

        raw_clkgates = {}
        raw_bits = {}
        raw_invs1 = {}
        raw_invs2 = {}

        for instance in instances:
            n = instance.getName()

            if clkgate_match := re.search(clkgate, n):
                i = int(clkgate_match[1])
                raw_clkgates[i] = raw_clkgates.get(i) or []
                raw_clkgates[i].append(instance)

            elif bit_match := re.search(bit, n):
                i = int(bit_match[1])
                raw_bits[i] = raw_bits.get(i) or []
                raw_bits[i].append(instance)

            elif inv1_match := re.search(inv1, n):
                i = int(inv1_match[1])
                raw_invs1[i] = raw_invs1.get(i) or []
                raw_invs1[i].append(instance)

            elif inv2_match := re.search(inv2, n):
                i = int(inv2_match[1])
                raw_invs2[i] = raw_invs2.get(i) or []
                raw_invs2[i].append(instance)

            elif clkgateand_match := re.search(clkgateand, n):
                self.clkgateand = instance

            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.clkgates = grouped_sorted(raw_clkgates)
        self.invs1 = grouped_sorted(raw_invs1)
        self.invs2 = grouped_sorted(raw_invs2)
        self.bits = grouped_sorted(
                {k: Bit(v) for k, v in raw_bits.item()})

    def place(self, row_list, start_row=0):
        r = row_list[start_row]
        for i in range(4):
            # to make the clkgateand an equal distance from all
            # gates that need its output
            if i == 2:
                r.place(self.clkgateand)

            r.place(self.invs1[i])
            r.place(self.invs2[i])
            r.place(self.clkgates[i])
            for j in range(8):
                r.place(self.bits[i*8+j])
        return start_row + 1

    def word_count(self):
        return 1


class DFFRF(Placeable): # 32 words
    def __init__(self, instances):

        raw_words = {}
        raw_decoders2x4 = {}
        raw_decoders3x8 = {}

        word = r"\FILE\\\[(\d+)\\\]\.RFW"
        decoder2x4 = r"\bDEC(\d+)\.D\b"
        decoder3x8 = r"\bDEC(\d+)\.D(\d+)\b"

        raw_rfw0_ties = {}
        raw_rfw0_invs1 = {}
        raw_rfw0_invs2 = {}
        raw_rfw0_obufs1 = {}
        raw_rfw0_obufs2 = {}

        rfw0_tie = r"\bRFW0\.TIE\\\[(\d+)\\\]\b"
        rfw0_inv1 = r"\bRFW0\.INV1\\\[(\d+)\\\]\b"
        rfw0_inv2 = r"\bRFW0\.INV2\\\[(\d+)\\\]\b"
        rfw0_obuf1 = r"\bRFW0\.BIT\\\[(\d+)\\\]\.OBUF1\b"
        rfw0_obuf2 = r"\bRFW0\.BIT\\\[(\d+)\\\]\.OBUF2\b"

        for instance in instances:
            n = instance.getName()

            if word_match := re.search(word, n):
                i = int(word_match[1])
                raw_words[i] = raw_words.get(i) or []
                raw_words[i].append(instance)

            elif decoder3x8_match := re.search(decoder3x8, n):
                i = int(decoder3x8_match[1])
                raw_decoders3x8[i] = raw_decoders3x8.get(i) or []
                raw_decoders3x8[i].append(instance)

            elif decoder2x4_match := re.search(decoder2x4, n):
                i = int(decoder2x4_match[1])
                raw_decoders2x4[i] = raw_decoders2x4.get(i) or []
                raw_decoders2x4[i].append(instance)

            elif rfw0_obuf_match1 := re.search(rfw0_obuf1, n):
                bit = int(rfw0_obuf_match1[1])
                raw_rfw0_obufs1[bit] = raw_rfw0_obufs1.get(bit) or []
                raw_rfw0_obufs1[bit].append(instance)

            elif rfw0_obuf_match2 := re.search(rfw0_obuf2, n):
                bit = int(rfw0_obuf_match2[1])
                raw_rfw0_obufs2[bit] = raw_rfw0_obufs2.get(bit) or []
                raw_rfw0_obufs2[bit].append(instance)

            elif rfw0_tie_match := re.search(rfw0_tie, n):
                i = int(tie_match[1])
                raw_rfw0_ties[i] = raw_rfw0_ties.get(i) or []
                raw_rfw0_ties[i].append(instance)

            elif rfw0_inv1_match := re.search(rfw0_inv1, n):
                i = int(inv1_match[1])
                raw_invs1[i] = raw_invs1.get(i) or []
                raw_invs1[i].append(instance)

            elif rfw0_inv2_match := re.search(rfw0_inv2, n):
                i = int(inv2_match[1])
                raw_invs2[i] = raw_invs2.get(i) or []
                raw_invs2[i].append(instance)

            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.words = grouped_sorted({k: Word(v) for k, v in raw_words.item()})
        self.decoders2x4 = grouped_sorted({k: Decoder2x4(v) for k, v in raw_decoders2x4.items()})
        self.decoders3x8 = grouped_sorted({k: Decoder3x8(v) for k, v in raw_decoders3x8.items()})

        self.rfw0_ties = grouped_sorted(raw_rfw0_ties)
        self.rfw0_invs1 = grouped_sorted(raw_rfw0_invs1)
        self.rfw0_invs2 = grouped_sorted(raw_rfw0_invs2)
        self.rfw0_obufs1 = grouped_sorted(raw_rfw0_obufs1)
        self.rfw0_obufs2 = grouped_sorted(raw_rfw0_obufs2)

    def place(self, row_list, start_row=0):

        current_row = start_row
        r = row_list[current_row]

        for i in range(32):
            if i % 8 == 0: # range(4)
                r.place(self.rfw0_invs1[i])
            r.place(self.rfw0_obufs1[i])

            if i % 4 == 0: # range(8)
                r.place(self.rfw0_ties[i])

            if i % 8 == 0: # range(4)
                r.place(self.rfw0_invs2[i])
            r.place(self.rfw0_obufs2[i])

        current_row += 1

        r = row_list[current_row]
        for aword in self.words:
            r.place(aword)

        return current_row + 1

    def word_count(self):
        return 32

class Decoder5x32(Placeable):
    def __init__(self, instances):
        self.enbuf = None

        raw_abufs = {}
        raw_and_gates = {}

        self.abufs = []
        self.and_gates = []

        dec3x8 = r"\bDEC(\d+)\b"
        dec4x2_comps = r"\bDEC\b"

        for instance in instances:
            n = instance.getName()

            if dec3x8_match := re.search(dec3x8, n):
                i = int(dec3x8_match[1])
                dec3x8[i].append(instance)
            elif dec4x2_comps_match := re.search(dec4x2_comps, n):
                i = int(dec4x2_comps_match[1])
                dec4x2_comps.append(instance)
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.dec3x8 = Decoder3x8(dec3x8)
        self.dec4x2_comps = grouped_sorted(dec4x2_comps)

    def place(self, row_list, start_row=0):
        """
        By placing this decoder, you agree that rows[start_row:start_row+7]
        are at the sole mercy of this function.
        """

        ands_placeable = self.and_gates
        buffers_placeable = [*self.abufs, self.enbuf, None, None, None, None]

        for i in range(8):
            r = row_list[start_row + i]

            r.place(ands_placeable[i])
            if buf := buffers_placeable[i]:
                r.place(buf)

        return start_row + 8

class Decoder3x8(Placeable):
    def __init__(self, instances):
        self.enbuf = None

        raw_abufs = {}
        raw_and_gates = {}

        self.abufs = []
        self.and_gates = []

        dand = r"\bAND(\d+)\b"
        abuf = r"\bABUF\\\[(\d+)\\\]"
        enbuf = r"\bENBUF\b"

        for instance in instances:
            n = instance.getName()

            if and_match := re.search(dand, n):
                i = int(and_match[1])
                raw_and_gates[i] = instance
            elif abuf_match := re.search(abuf, n):
                i = int(abuf_match[1])
                raw_abufs[i] = instance
            elif enbuf_match := re.search(enbuf, n):
                self.enbuf = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.and_gates = grouped_sorted(raw_and_gates)
        self.abufs = grouped_sorted(raw_abufs)

    def place(self, row_list, start_row=0):
        """
        By placing this decoder, you agree that rows[start_row:start_row+7]
        are at the sole mercy of this function.
        """

        ands_placeable = self.and_gates
        buffers_placeable = [*self.abufs, self.enbuf, None, None, None, None]

        for i in range(8):
            r = row_list[start_row + i]

            r.place(ands_placeable[i])
            if buf := buffers_placeable[i]:
                r.place(buf)

        return start_row + 8
