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
from .util import d2a, sarv
from .row import Row
from .placeable import Placeable, DataError, RegExp

from opendbpy import dbInst as Instance

import re
import sys
import math
from types import SimpleNamespace as NS
from functools import partial
from typing import Callable, List, Dict, Union, TextIO
from itertools import zip_longest

# --

P = Placeable

class Mux(Placeable):
    """
    Constraint: The number of selection buffers is necessarily == the number of bytes.
    """
    def __init__(self, instances: List[Instance]):
        self.sel_diodes: List[Instance] = None

        # First access is the byte
        self.selbufs: List[List[Instance]] = None
        self.muxes: List[List[Instance]] = None
        self.input_diodes: List[List[List[Instance]]] = None

        raw_sel_diodes: Dict[int, Instance] = {}
        raw_selbufs: Dict[int, Dict[int, Instance]] = {}
        raw_muxes: Dict[int, Dict[int, Instance]] = {}
        raw_input_diodes: Dict[int, Dict[int, Dict[int, Instance]]] = {}

        m = NS()
        r = self.regexes()
        for instance in instances:
            n = instance.getName()
            if sarv(m, "selbuf_match", re.search(r.selbuf, n)):
                line, byte = (int(m.selbuf_match[1] or "0"), int(m.selbuf_match[2]))
                raw_selbufs[byte] = raw_selbufs.get(byte) or {}
                raw_selbufs[byte][line] = instance
            elif sarv(m, "ind_match", re.search(r.input_diode, n)):
                byte, input, bit = (int(m.ind_match[1]), int(m.ind_match[2]), int(m.ind_match[3]))
                raw_input_diodes[byte] = raw_input_diodes.get(byte) or {}
                raw_input_diodes[byte][input] = raw_input_diodes[byte].get(input) or {}
                raw_input_diodes[byte][input][bit] = instance
            elif sarv(m, "mux_match", re.search(r.mux, n)):
                byte, bit = (int(m.mux_match[1]), int(m.mux_match[2]))
                raw_muxes[byte] = raw_muxes.get(byte) or {}
                raw_muxes[byte][bit] = instance
            elif sarv(m, "seld_match", re.search(r.sel_diode, n)):
                line = int(m.seld_match[1])
                raw_sel_diodes[line] = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.selbufs = d2a({k: d2a(v) for k, v in raw_selbufs.items()})
        self.muxes = d2a({k: d2a(v) for k, v in raw_muxes.items()})
        self.input_diodes = d2a({k: d2a({k2: d2a(v2) for k2, v2 in v.items()}) for k, v in raw_input_diodes.items()})
        self.sel_diodes = d2a(raw_sel_diodes)

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

        return current_row + 1

class Bit(Placeable):
    def __init__(self, instances: List[Instance]):
        self.store = None
        self.obufs = None
        
        raw_obufs: Dict[int, Instance] = {}

        m = NS()
        r = self.regexes()
        for instance in instances:
            n = instance.getName()

            if sarv(m, "ff_match", re.search(r.ff, n)):
                self.store = instance
            elif sarv(m, "obuf_match", re.search(r.obuf, n)):
                port = int(m.obuf_match[1] or "0")
                raw_obufs[port] = instance
            elif sarv(m, "latch_match", re.search(r.latch, n)):
                self.store = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.obufs = d2a(raw_obufs)

    def place(self, row_list: List[Row], start_row: int = 0):
        r = row_list[start_row]

        r.place(self.store)
        for obuf in self.obufs:
            r.place(obuf)

        return start_row

class Byte(Placeable):
    def __init__(self, instances: List[Instance]):
        self.clockgate: Instance = None
        self.cgand: Instance = None
        self.clkinv: Instance = None
        self.clkdiode: Instance = None
        self.bits: List[Bit] = None
        self.selinvs: List[Instance] = None
        
        raw_bits: Dict[int, List[Instance]] = {}
        raw_selinvs: Dict[int, Instance] = {}

        m = NS()
        r = self.regexes()

        for instance in instances:
            n = instance.getName()

            if sarv(m, "bit_match", re.search(r.bit, n)):
                i = int(m.bit_match[1])
                raw_bits[i] = raw_bits.get(i) or []
                raw_bits[i].append(instance)
            elif sarv(m, "cg_match", re.search(r.cg, n)):
                self.clockgate = instance
            elif sarv(m, "cgand_match", re.search(r.cgand, n)):
                self.cgand = instance
            elif sarv(m, "selinv_match", re.search(r.selinv, n)):
                port = int(m.selinv_match[1] or "0")
                raw_selinvs[port] = instance
            elif sarv(m, "clkinv_match", re.search(r.clkinv, n)):
                self.clkinv = instance
            elif sarv(m, "clkd_match", re.search(r.clk_diode, n)):
                self.clkdiode = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.bits = d2a({k: Bit(v) for k, v in raw_bits.items()})
        self.selinvs = d2a(raw_selinvs)

    def place(self, row_list: List[Row], start_row: int = 0):
        r = row_list[start_row]

        for bit in self.bits:
            bit.place(row_list, start_row)

        r.place(self.clockgate)
        r.place(self.cgand)
        r.place(self.clkdiode)
        for selinv in self.selinvs:
            r.place(selinv)
        if self.clkinv is not None:
            r.place(self.clkinv)

        return start_row

class Word(Placeable):
    def __init__(self, instances: List[Instance]):
        self.clkbuf: Instance = None
        self.bytes: List[Byte] = None
        self.selbufs: List[Instance] = None

        raw_selbufs: Dict[int, Instance] = {}
        raw_bytes: Dict[int, List[Instance]] = {}

        m = NS()
        r = self.regexes()

        for instance in instances:
            n = instance.getName()

            if sarv(m, "byte_match", re.search(r.byte, n)):
                i = int(m.byte_match[1])
                raw_bytes[i] = raw_bytes.get(i) or []
                raw_bytes[i].append(instance)
            elif sarv(m, "sb_match", re.search(r.selbuf, n)):
                port = int(m.sb_match[1] or "0")
                raw_selbufs[port] = instance
            elif sarv(m, "cb_match", re.search(r.clkbuf, n)):
                self.clkbuf = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.bytes = d2a({k: Byte(v) for k, v in raw_bytes.items()})
        self.selbufs = d2a(raw_selbufs)

    def place(self, row_list: List[Row], start_row: int = 0):
        r = row_list[start_row]

        for byte in self.bytes:
            byte.place(row_list, start_row)

        r.place(self.clkbuf)
        for selbuf in self.selbufs:
            r.place(selbuf)

        return start_row + 1

    def word_count(self):
        return 1

class Decoder3x8(Placeable):
    def __init__(self, instances: List[Instance]):
        self.enbuf: Instance = None
        self.and_gates: List[Instance] = None
        self.abufs: List[Instance] = None

        raw_abufs: Dict[int, Instance] = {}
        raw_and_gates: Dict[int, Instance] = {}

        m = NS()
        r = self.regexes()

        for instance in instances:
            n = instance.getName()

            if sarv(m, "and_match", re.search(r.dand, n)):
                i = int(m.and_match[1])
                raw_and_gates[i] = instance
            elif sarv(m, "abuf_match", re.search(r.abuf, n)):
                i = int(m.abuf_match[1])
                raw_abufs[i] = instance
            elif sarv(m, "enbuf_match", re.search(r.enbuf, n)):
                self.enbuf = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.and_gates = d2a(raw_and_gates)
        self.abufs = d2a(raw_abufs)

    def place(self, row_list: List[Row], start_row: int = 0):
        """
        By placing this decoder, you agree that rows[start_row:start_row+7]
        are at the sole mercy of this function.
        """

        ands_placeable = self.and_gates
        buffers_placeable = [*self.abufs, self.enbuf, None, None, None, None]

        for i in range(8):
            r = row_list[start_row + i]

            r.place(ands_placeable[i])
            buf = buffers_placeable[i]
            if buf is not None:
                r.place(buf)

        return start_row + 8

class Slice(Placeable): # A slice is defined as 8 words.
    def __init__(self, instances: List[Instance]):
        self.webufs: List[Instance] = []
        self.clkbuf: Instance = None
        self.decoders: List[Decoder3x8] = None
        self.words: List[Word] = None

        raw_words: Dict[int, List[Instance]] = {}
        raw_decoders: Dict[int, List[Instance]] = {} # One per port.

        m = NS()
        r = self.regexes()

        for instance in instances:
            n = instance.getName()

            if sarv(m, "word_match", re.search(r.word, n)):
                i = int(m.word_match[1])
                raw_words[i] = raw_words.get(i) or []
                raw_words[i].append(instance)
            elif sarv(m, "d_match", re.search(r.decoder, n)):
                port = int(m.d_match[1] or "0")
                raw_decoders[port] = raw_decoders.get(port) or []
                raw_decoders[port].append(instance)
            elif sarv(m, "wb_match", re.search(r.webuf, n)):
                self.webufs.append(instance) # Shouldn't this have the indices involved in some aspect?
            elif sarv(m, "cb_match", re.search(r.clkbuf, n)):
                self.clkbuf = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.decoders = d2a({k: Decoder3x8(v) for k, v in raw_decoders.items()})
        self.words = d2a({k: Word(v) for k, v in raw_words.items()})

        word_count = len(self.words)
        if word_count != 8:
            raise DataError("Slice has (%i/8) words." % word_count)

    def place(self, row_list: List[Row], start_row: int = 0):
        """
        Decoders for odd addressing ports are placed on the left,
        and for even addressing ports are placed on the right.

        This is to avoid congestion.
        """
        # Prologue. Split vertical elements into left and right columns
        vertical_left = []
        vertical_right = []
        right = True

        for decoder in self.decoders:
            target = vertical_right if right else vertical_left
            target.append(decoder)
            right = not right

        final_rows = []

        # Act 1. Place Left Vertical Elements
        current_row = start_row
        for decoder in vertical_left:
            current_row = decoder.place(row_list, start_row)

        final_rows.append(current_row)

        # Act 2. Place Horizontal Elements
        current_row = start_row
        for word in self.words:
            current_row = word.place(row_list, current_row)

        Row.fill_rows(row_list, start_row, current_row)

        place_clkbuf_alone = False
        last_column = [*self.webufs]
        if len(last_column) == 8:
            place_clkbuf_alone = True
        else:
            last_column.append(self.clkbuf)

        while len(last_column) < 8:
            last_column.append(None)

        for i in range(8):
            r = row_list[start_row + i]
            if last_column[i] is not None:
                r.place(last_column[i])

        if place_clkbuf_alone:
            row_list[start_row].place(self.clkbuf)

        Row.fill_rows(row_list, start_row, current_row)

        final_rows.append(current_row)

        # Act 3. Place Right Vertical Elements
        current_row = start_row
        for decoder in vertical_right:
            current_row = decoder.place(row_list, start_row)

        #Row.fill_rows(row_list, start_row, current_row)
        final_rows.append(current_row)

        # Epilogue
        max_row = max(*final_rows)
        # Row.fill_rows(row_list, start_row, max_row)
        return max_row

    def word_count(self):
        return 8

class LRPlaceable(Placeable):
    """
    A Placeable that can have some of its elements placed in left & right columns.

    This is to make the design more routable.
    """

    def lrplace(self, row_list: List[Row], start_row: int, addresses: int, common: List[Instance], port_elements: List[str], place_horizontal_elements: Callable) -> int:
        # Prologue. Split vertical elements into left and right columns
        chunks = []
        chunk_count = math.ceil(addresses / 2)
        per_chunk = math.ceil(len(common) / chunk_count)

        i = 0
        while i < len(common):
            chunks.append(common[i: i + per_chunk])
            i += per_chunk

        vertical_left = []
        vertical_right = []
        right = True

        for i in range(0, addresses):
            target = vertical_right if right else vertical_left
            column = []
            for accessor in port_elements:
                elements: Union[List[Instance], Instance] = getattr(self, accessor)
                if len(elements) == 0:
                    continue
                element = elements[i]
                if isinstance(element, list):
                    column += element
                else:
                    column.append(element)
            if right and len(chunks):
                column += chunks[i // 2]
            target.append(column)
            right = not right
        
        final_rows = []

        # Act 1. Place Left Vertical Elements
        current_row = start_row

        for column in vertical_left:
            current_row = start_row
            for el in column:
                r = row_list[current_row]
                r.place(el)
                current_row += 1

        Row.fill_rows(row_list, start_row, current_row)

        final_rows.append(current_row)

        # Act 2. Place Horizontal Elements
        current_row = place_horizontal_elements(start_row)

        #Row.fill_rows(row_list, start_row, current_row)

        final_rows.append(current_row)

        # Act 3. Place Right Vertical Elements
        for column in vertical_right:
            current_row = start_row
            for el in column:
                r = row_list[current_row]
                r.place(el)
                current_row += 1

        final_rows.append(current_row)

        # Epilogue
        max_row = max(*final_rows)
        #Row.fill_rows(row_list, start_row, max_row)
        return max_row

class Block(LRPlaceable): # A block is defined as 4 slices (32 words)
    def __init__(self, instances: List[Instance]):
        self.clk_diode: Instance = None
        self.clkbuf: Instance = None

        self.dibufs: List[Instance] = None
        self.webufs: List[Instance] = None

        self.slices: List[Slice]  = None

        # These sets of buffers are duplicated once per read port,
        # so the first access always picks the port.
        self.decoder_ands: List[List[Instance]] = None
        self.enbufs: List[Instance] = None
        self.dobufs: List[List[Instance]] = None
        self.a_diodes: List[List[Instance]] = None
        self.abufs: List[List[Instance]] = None
        self.fbufenbufs: List[List[Instance]] = None
        ## Floatbufs are grouped further: there are a couple of floatbufs per tie cell.
        self.ties: List[List[Instance]] = None
        self.floatbufs: List[List[List[Instance]]] = None 

        raw_enbufs: Dict[int, Instance] = {}

        raw_slices: Dict[int, List[Instance]] = {}
        raw_decoder_ands: Dict[int, Dict[int, Instance]] = {}

        raw_dibufs: Dict[int, Instance] = {}
        raw_dobufs: Dict[int, Dict[int, Instance]] = {}
        raw_dobuf_diodes: Dict[int, Dict[int, Instance]] = {}

        raw_webufs: Dict[int, Instance] = {}
        
        raw_a_diodes: Dict[int, Dict[int, Instance]] = {}
        raw_abufs: Dict[int, Dict[int, Instance]] = {}

        raw_ties: Dict[int, Dict[int, Instance]] = {}
        raw_fbufenbufs: Dict[int, Dict[int, Instance]] = {}
        raw_floatbufs: Dict[int, Dict[int, Dict[int, Instance]]] = {}

        m = NS()
        r = self.regexes()
        for instance in instances:
            n = instance.getName()

            if sarv(m, "slice_match", re.search(r.slice, n)):
                i = int(m.slice_match[1])
                raw_slices[i] = raw_slices.get(i) or []
                raw_slices[i].append(instance)
            elif sarv(m, "decoder_and_match", re.search(r.decoder_and, n)):
                port = int(m.decoder_and_match[1] or "0")
                i = int(m.decoder_and_match[2])
                raw_decoder_ands[port] = raw_decoder_ands.get(port) or {}
                raw_decoder_ands[port][i] = instance
            elif sarv(m, "dibuf_match", re.search(r.dibuf, n)):
                i = int(m.dibuf_match[1])
                raw_dibufs[i] = instance
            elif sarv(m, "webuf_match", re.search(r.webuf, n)):
                i = int(m.webuf_match[1])
                raw_webufs[i] = instance
            elif sarv(m, "clk_match", re.search(r.clk_diode, n)):
                self.clk_diode = instance
            elif sarv(m, "clkbuf_match", re.search(r.clkbuf, n)):
                self.clkbuf = instance
            elif sarv(m, "a_matches", re.search(r.a_diode, n)):
                port = int(m.a_matches[1] or "0")
                i = int(m.a_matches[2])
                raw_a_diodes[port] = raw_a_diodes.get(port) or {}
                raw_a_diodes[port][i] = instance
            elif sarv(m, "abuf_match", re.search(r.abuf, n)):
                port = int(m.abuf_match[1] or "0")
                i = int(m.abuf_match[2])
                raw_abufs[port] = raw_abufs.get(port) or {}
                raw_abufs[port][i] = instance
            elif sarv(m, "enbuf_match", re.search(r.enbuf, n)):
                port = int(m.enbuf_match[1] or "0")
                raw_enbufs[port] = instance
            elif sarv(m, "tie_match", re.search(r.tie, n)):
                port = int(m.tie_match[1] or "0")
                i = int(m.tie_match[2])
                raw_ties[port] = raw_ties.get(port) or {}
                raw_ties[port][i] = instance
            elif sarv(m, "fbufenbuf_match", re.search(r.fbufenbuf, n)):
                port = int(m.fbufenbuf_match[1] or "0")
                i = int(m.fbufenbuf_match[2])
                raw_fbufenbufs[port] = raw_fbufenbufs.get(port) or {}
                raw_fbufenbufs[port][i] = instance
            elif sarv(m, "floatbuf_match", re.search(r.floatbuf, n)):
                byte, port, bit = (int(m.floatbuf_match[1]), int(m.floatbuf_match[2] or "0"), int(m.floatbuf_match[3]))
                raw_floatbufs[port] = raw_floatbufs.get(port) or {}
                raw_floatbufs[port][byte] = raw_floatbufs[port].get(byte) or {}
                raw_floatbufs[port][byte][bit] = instance
            elif sarv(m, "dobuf_match", re.search(r.dobuf, n)):
                port = int(m.dobuf_match[1] or "0")
                i = int(m.dobuf_match[2])
                raw_dobufs[port] = raw_dobufs.get(port) or {}
                raw_dobufs[port][i] = instance
            elif sarv(m, "dobufd_match", re.search(r.dobuf_diode, n)):
                port = int(m.dobufd_match[1] or "0")
                i = int(m.dobufd_match[2])
                raw_dobuf_diodes[port] = raw_dobuf_diodes.get(port) or {}
                raw_dobuf_diodes[port][i] = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.slices = d2a({k: Slice(v) for k, v in raw_slices.items()})

        self.decoder_ands = d2a({k: d2a(v) for k, v in raw_decoder_ands.items()})

        self.enbufs = d2a(raw_enbufs)
        self.dibufs = d2a(raw_dibufs)
        self.dobuf_diodes = d2a({k: d2a(v) for k, v in raw_dobuf_diodes.items()})
        self.dobufs = d2a({k: d2a(v) for k, v in raw_dobufs.items()})

        self.webufs = d2a(raw_webufs)
        self.abufs = d2a({k: d2a(v) for k, v in raw_abufs.items()})

        self.fbufenbufs = d2a({k: d2a(v) for k, v in raw_fbufenbufs.items()})

        self.ties = d2a({k: d2a(v) for k, v in raw_ties.items()})
        self.floatbufs = d2a({k: d2a({k: d2a(v2) for k, v2 in v.items()}) for k, v in raw_floatbufs.items()})
        self.a_diodes = d2a({k: d2a(v) for k, v in raw_a_diodes.items()})


    def place(self, row_list: List[Row], start_row: int = 0):
        def place_horizontal_elements(start_row: int):
            current_row = start_row
            r = row_list[current_row]

            for dibuf in self.dibufs:
                r.place(dibuf)

            current_row += 1

            for slice in self.slices:
                current_row = slice.place(row_list, current_row)

            port_count = len(self.ties)

            for port in range(port_count):
                r = row_list[current_row]
                for tie_group, tie in enumerate(self.ties[port]):
                    r.place(tie)
                    for floatbuf in self.floatbufs[port][tie_group]:
                        r.place(floatbuf)
            
            current_row += 1

            for port in range(port_count):
                r = row_list[current_row]
                dobufs = self.dobufs[port]
                dobuf_diodes = self.dobuf_diodes[port]
                for dobuf, diode in zip(dobufs, dobuf_diodes):
                    r.place(dobuf)
                    r.place(diode)
                current_row += 1

            return current_row
        
        return self.lrplace(
            row_list=row_list,
            start_row=start_row,
            addresses=len(self.abufs),
            common=[
                self.clk_diode,
                self.clkbuf,
                *self.webufs
            ],
            port_elements=[
                "enbufs",
                "a_diodes",
                "abufs",
                "decoder_ands",
                "fbufenbufs"
            ],
            place_horizontal_elements=place_horizontal_elements
        )

    def word_count(self):
        return 32

class HigherLevelPlaceable(LRPlaceable):
    def __init__(self, instances: List[Instance], block_size: int):
        self.clkbuf: Instance = None
        
        self.di_diode: List[Instance] = None
        self.dibufs: List[Instance] = None

        self.webufs: List[Instance] = None

        self.blocks: List[Union[Block, HigherLevelPlaceable]] = None
        
        # These sets of buffers are duplicated once per read port,
        # so the first access always picks the port.
        self.a_diodes: List[List[Instance]] = None
        self.decoder_ands: List[List[Instance]] = None
        self.enbufs: List[Instance] = None
        self.domuxes: List[Mux] = None
        self.abufs: List[List[Instance]] = None

        # --
        raw_di_diodes: Dict[int, Instance] = {}
        raw_dibufs: Dict[int, Instance] = {}
        raw_webufs: Dict[int, Instance] = {}

        raw_blocks: Dict[int, List[Instance]] = {}

        raw_decoder_ands: Dict[int, Dict[int, Instance]] = {}
        raw_enbufs: Dict[int, Instance] = {}
        raw_domuxes: Dict[int, List[Instance]] = {}

        raw_a_diodes: Dict[int, Dict[int, Instance]] = {}
        raw_abufs: Dict[int, Dict[int, Instance]] = {}

        m = NS()
        r = self.regexes()

        for instance in instances:
            n = instance.getName()
            if sarv(m, "block_match", re.search(getattr(r, str(block_size)), n)):
                i = int(m.block_match[1])
                raw_blocks[i] = raw_blocks.get(i) or []
                raw_blocks[i].append(instance)
            elif sarv(m, "decoder_and_match", re.search(r.decoder_and, n)):
                port = int(m.decoder_and_match[1] or "0")
                i = int(m.decoder_and_match[2])
                raw_decoder_ands[port] = raw_decoder_ands.get(port) or {}
                raw_decoder_ands[port][i] = instance
            elif sarv(m, "did_match", re.search(r.di_diode, n)):
                i = int(m.did_match[1])
                raw_di_diodes[i] = instance
            elif sarv(m, "dibuf_match", re.search(r.dibuf, n)):
                i = int(m.dibuf_match[1])
                raw_dibufs[i] = instance
            elif sarv(m, "webuf_match", re.search(r.webuf, n)):
                i = int(m.webuf_match[1])
                raw_webufs[i] = instance
            elif sarv(m, "clkbuf_match", re.search(r.clkbuf, n)):
                self.clkbuf = instance
            elif sarv(m, "a_matches", re.search(r.a_diode, n)):
                port = int(m.a_matches[1] or "0")
                i = int(m.a_matches[2])
                raw_a_diodes[port] = raw_a_diodes.get(port) or {}
                raw_a_diodes[port][i] = instance
            elif sarv(m, "abuf_match", re.search(r.abuf, n)):
                port = int(m.abuf_match[1] or "0")
                i = int(m.abuf_match[2])
                raw_abufs[port] = raw_abufs.get(port) or {}
                raw_abufs[port][i] = instance
            elif sarv(m, "enbuf_match", re.search(r.enbuf, n)):
                port = int(m.enbuf_match[1] or "0")
                raw_enbufs[port] = instance
            elif sarv(m, "domux_match", re.search(r.domux, n)):
                port = int(m.domux_match[1] or "0")
                raw_domuxes[port] = raw_domuxes.get(port) or []
                raw_domuxes[port].append(instance)
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.di_diodes = d2a(raw_di_diodes)
        self.dibufs = d2a(raw_dibufs)
        self.webufs = d2a(raw_webufs)

        self.blocks = d2a({k: create_hierarchy(v, block_size) for k, v in
            raw_blocks.items()})

        self.decoder_ands = d2a({k: d2a(v) for k, v in raw_decoder_ands.items()})
        self.enbufs = d2a(raw_enbufs)
        self.domuxes = d2a({ k: Mux(v) for k, v in raw_domuxes.items()})
        self.abufs = d2a({k: d2a(v) for k, v in raw_abufs.items()})
        self.a_diodes = d2a({k: d2a(v) for k, v in raw_a_diodes.items()})

    def place(self, row_list: List[Row], start_row: int = 0):
        def symmetrically_placeable():
            return self.word_count() > 128
        
        current_row = start_row

        def place_horizontal_elements(start_row: int):
            # all of the big designs include 4 instances
            # of the smaller block they are constituted of
            # so they can all be 1:1 if they are 2x2
            # the smallest 1:1 is the 128 word block
            # it is placed all on top of each other
            current_row = start_row
            r = row_list[current_row]

            for diode, dibuf in zip(self.di_diodes, self.dibufs):
                r.place(diode)
                r.place(dibuf)

            current_row += 1

            partition_cap = int(math.sqrt(len(self.blocks)))
            if symmetrically_placeable():
                for i in range(len(self.blocks)):
                    if i == partition_cap:
                        current_row = start_row
                    current_row = self.blocks[i].place(row_list, current_row)
            else:
                for block in self.blocks:
                    current_row = block.place(row_list, current_row)

            for domux in self.domuxes:
                current_row = domux.place(row_list, current_row)

            return current_row

        return self.lrplace(
            row_list=row_list,
            start_row=current_row,
            addresses=len(self.domuxes),
            common=[
                *([self.clkbuf] if self.clkbuf is not None else []),
                *self.webufs
            ],
            port_elements=[
                "enbufs",
                "abufs",
                "a_diodes",
                "decoder_ands"
            ],
            place_horizontal_elements=place_horizontal_elements
        )

    def word_count(self):
        return len(self.blocks) * (self.blocks[0].word_count())

def create_hierarchy(instances, word_count):
    hierarchy = None
    if word_count == 1:
        hierarchy = Word(instances)
    elif word_count == 8:
        hierarchy = Slice(instances)
    elif word_count == 32:
        hierarchy = Block(instances)
    else:
        """
        I derived this equation based on the structure we have.
        Feel free to independently verify it.

        Valid for 128 <= 𝒙 <= 2048:

            𝒇(𝒙) = 32 * 4 ^ ⌈log2(𝒙 / 128) / 2⌉
        """
        def f(x):
            return 32 * (4 ** math.ceil(math.log2(x / 128) / 2))
        block_size = f(word_count)
        hierarchy = HigherLevelPlaceable(instances, block_size)
    return hierarchy