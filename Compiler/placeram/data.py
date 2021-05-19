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

from .util import d2a, Bunch
from .row import Row

from opendbpy import dbInst
Instance = dbInst

import os
import re
import sys
import yaml
import math
from functools import partial
from typing import List, Dict, Union, TextIO, Optional
# --
RegExp = str

RegexDictionary: Dict[str, Dict[str, RegExp]] = yaml.safe_load(
    open(os.path.join(os.path.dirname(__file__), "rx.yml"))
)
def override_regex_dict(override_dict: Dict[str, RegExp]):
    global RegexDictionary
    for key, value in override_dict.items():
        class_name, regex = key.split(".")
        RegexDictionary[class_name][regex] = value

Representable = Union[Instance, 'Placeable',  List['Representable']]

class Placeable(object):
    def place(self, row_list: List[Row], start_row: int = 0):
        raise Exception("Method unimplemented.")

    def represent(self, tab_level: int = -1, file: TextIO = sys.stderr):
        raise Exception("Method unimplemented.")

    def word_count(self):
        raise Exception("Method unimplemented.")

    def regexes(self) -> Bunch:
        """
        Returns a dictionary of regexes for this class accessible with the dot
        notation.
        """
        return Bunch(RegexDictionary[self.__class__.__name__])

    @staticmethod
    def represent_instance(
        name: str,
        instance: Instance,
        tab_level: int,
        file: TextIO = sys.stderr
    ):
        """
        Writes textual representation of an instance to `file`.
        """
        if name != "":
            name += " "
        str_instance = "[I<%s> '%s']" % (instance.getMaster().getName(), instance.getName())
        print("%s%s%s" % ("".join(["  "] * tab_level), name, str_instance), file=file)

    ri = represent_instance

    @staticmethod
    def represent_array(
        name: str,
        array: List[Representable],
        tab_level: int,
        file: TextIO = sys.stderr,
        header: Optional[str] = None
    ):
        """
        Writes textual representation of a list of 'representables' to `file`.

        A representable is an Instance, a Placeable or a list of representables.
        It's a recursive type definition.
        """
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
    def __init__(self, instances: List[Instance]):
        self.store = None
        self.obufs = None
        
        raw_obufs: Dict[int, Instance] = {}

        r = self.regexes()
        for instance in instances:
            n = instance.getName()

            if ff_match := re.search(r.ff, n):
                self.store = instance
            elif obuf_match := re.search(r.obuf, n):
                port = int(obuf_match[1] or "0")
                raw_obufs[port] = instance
            elif latch_match := re.search(r.latch, n):
                self.store = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.obufs = d2a(raw_obufs)

    def represent(self, tab_level: int = -1, file: TextIO = sys.stderr):
        tab_level += 1

        P.ri("Storage Element", self.store, tab_level, file)
        P.ra("Output Buffers", self.obufs, tab_level, file)

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
        self.bits: List[Bit] = None
        self.selinvs: List[Instance] = None
        
        raw_bits: Dict[int, List[Instance]] = {}
        raw_selinvs: Dict[int, Instance] = {}

        r = self.regexes()

        for instance in instances:
            n = instance.getName()

            if bit_match := re.search(r.bit, n):
                i = int(bit_match[1])
                raw_bits[i] = raw_bits.get(i) or []
                raw_bits[i].append(instance)
            elif cg_match := re.search(r.cg, n):
                self.clockgate = instance
            elif cgand_match := re.search(r.cgand, n):
                self.cgand = instance
            elif selinv_match := re.search(r.selinv, n):
                port = int(selinv_match[1] or "0")
                raw_selinvs[port] = instance
            elif clkinv_match := re.search(r.clkinv, n):
                self.clkinv = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.bits = d2a({k: Bit(v) for k, v in raw_bits.items()})
        self.selinvs = d2a(raw_selinvs)

    def represent(self, tab_level: int = -1, file: TextIO = sys.stderr):
        tab_level += 1

        P.ri("Clock Gate", self.clockgate, tab_level, file)
        P.ri("Clock Gate AND", self.cgand, tab_level, file)
        P.ra("Selection Line Inverters", self.selinvs, tab_level, file)
        if self.clkinv is not None:
            P.ri("Clock Inverter", self.clkinv, tab_level, file)

        P.ra("Bits", self.bits, tab_level, file, header="Bit")

    def place(self, row_list: List[Row], start_row: int = 0):
        r = row_list[start_row]

        for bit in self.bits:
            bit.place(row_list, start_row)

        r.place(self.clockgate)
        r.place(self.cgand)
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

        r = self.regexes()

        for instance in instances:
            n = instance.getName()

            if byte_match := re.search(r.byte, n):
                i = int(byte_match[1])
                raw_bytes[i] = raw_bytes.get(i) or []
                raw_bytes[i].append(instance)
            elif sb_match := re.search(r.selbuf, n):
                port = int(sb_match[1] or "0")
                raw_selbufs[port] = instance
            elif cb_match := re.search(r.clkbuf, n):
                self.clkbuf = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.bytes = d2a({k: Byte(v) for k, v in raw_bytes.items()})
        self.selbufs = d2a(raw_selbufs)

    def represent(self, tab_level: int = -1, file: TextIO = sys.stderr):
        tab_level += 1

        P.ri("Clock Buffer", self.clkbuf, tab_level, file)
        P.ra("Selection Line Buffers", self.selbufs, tab_level, file)
        P.ra("Bytes", self.bytes, tab_level, file, header="Byte")

    def place(self, row_list: List[Row], start_row: int = 0):
        r = row_list[start_row]

        for byte in self.bytes:
            byte.place(row_list, start_row)

        r.place(self.clkbuf)
        for selbuf in self.selbufs:
            r.place(selbuf)

        return start_row

    def word_count(self):
        return 1

class Decoder3x8(Placeable):
    def __init__(self, instances: List[Instance]):
        self.enbuf: Instance = None
        self.and_gates: List[Instance] = None
        self.abufs: List[Instance] = None

        raw_abufs: Dict[int, Instance] = {}
        raw_and_gates: Dict[int, Instance] = {}

        r = self.regexes()

        for instance in instances:
            n = instance.getName()

            if and_match := re.search(r.dand, n):
                i = int(and_match[1])
                raw_and_gates[i] = instance
            elif abuf_match := re.search(r.abuf, n):
                i = int(abuf_match[1])
                raw_abufs[i] = instance
            elif enbuf_match := re.search(r.enbuf, n):
                self.enbuf = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.and_gates = d2a(raw_and_gates)
        self.abufs = d2a(raw_abufs)

    def represent(self, tab_level: int = -1, file: TextIO = sys.stderr):
        tab_level += 1

        P.ri("Enable Buffer", self.enbuf, tab_level, file)
        P.ra("AND Gates", self.and_gates, tab_level, file)
        P.ra("Addreess Buffers", self.abufs, tab_level, file)

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
            if buf := buffers_placeable[i]:
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

        r = self.regexes()
        for instance in instances:
            n = instance.getName()

            if word_match := re.search(r.word, n):
                i = int(word_match[1])
                raw_words[i] = raw_words.get(i) or []
                raw_words[i].append(instance)
            elif d_match := re.search(r.decoder, n):
                port = int(d_match[1] or "0")
                raw_decoders[port] = raw_decoders.get(port) or []
                raw_decoders[port].append(instance)
            elif wb_match := re.search(r.webuf, n):
                self.webufs.append(instance) # Shouldn't this have the indices involved in some aspect?
            elif cb_match := re.search(r.clkbuf, n):
                self.clkbuf = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.decoders = d2a({k: Decoder3x8(v) for k, v in raw_decoders.items()})
        self.words = d2a({k: Word(v) for k, v in raw_words.items()})

        word_count = len(self.words)
        if word_count != 8:
            raise DataError("Slice has (%i/8) words." % word_count)

    def represent(self, tab_level: int = -1, file: TextIO = sys.stderr):
        tab_level += 1

        P.ra("Decoders", self.decoders, tab_level, file, header="Decoder")
        P.ra("Write Enable Buffers", self.webufs, tab_level, file)
        P.ra("Words", self.words, tab_level, file, header="Word")

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
            word.place(row_list, current_row)
            current_row += 1

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

        Row.fill_rows(row_list, start_row, current_row)
        final_rows.append(current_row)

        # Epilogue 
        max_row = max(*final_rows)
        Row.fill_rows(row_list, start_row, max_row)
        return max_row

    def word_count(self):
        return 8

class Block(Placeable): # A block is defined as 4 slices (32 words)
    def __init__(self, instances: List[Instance]):
        self.clkbuf: Instance = None
        self.dibufs: List[Instance] = None
        self.webufs: List[Instance] = None

        self.slices: List[Slice]  = None

        # These sets of buffers are duplicated once per read port,
        # so the first access always picks the port.
        self.decoder_ands: List[List[Instance]] = None
        self.enbufs: List[Instance] = None
        self.dobufs: List[List[Instance]] = None
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

        raw_webufs: Dict[int, Instance] = {}

        raw_abufs: Dict[int, Dict[int, Instance]] = {}

        raw_ties: Dict[int, Dict[int, Instance]] = {}
        raw_fbufenbufs: Dict[int, Dict[int, Instance]] = {}
        raw_floatbufs: Dict[int, Dict[int, Dict[int, Instance]]] = {}

        r = self.regexes()
        for instance in instances:
            n = instance.getName()

            if slice_match := re.search(r.slice, n):
                i = int(slice_match[1])
                raw_slices[i] = raw_slices.get(i) or []
                raw_slices[i].append(instance)
            elif decoder_and_match := re.search(r.decoder_and, n):
                port = int(decoder_and_match[1] or "0")
                i = int(decoder_and_match[2])
                raw_decoder_ands[port] = raw_decoder_ands.get(port) or {}
                raw_decoder_ands[port][i] = instance
            elif dibuf_match := re.search(r.dibuf, n):
                i = int(dibuf_match[1])
                raw_dibufs[i] = instance
            elif webuf_match := re.search(r.webuf, n):
                i = int(webuf_match[1])
                raw_webufs[i] = instance
            elif clkbuf_match := re.search(r.clkbuf, n):
                self.clkbuf = instance
            elif abuf_match := re.search(r.abuf, n):
                port = int(abuf_match[1] or "0")
                i = int(abuf_match[2])
                raw_abufs[port] = raw_abufs.get(port) or {}
                raw_abufs[port][i] = instance
            elif enbuf_match := re.search(r.enbuf, n):
                port = int(enbuf_match[1] or "0")
                raw_enbufs[port] = instance
            elif tie_match := re.search(r.tie, n):
                port = int(tie_match[1] or "0")
                i = int(tie_match[2])
                raw_ties[port] = raw_ties.get(port) or {}
                raw_ties[port][i] = instance
            elif fbufenbuf_match := re.search(r.fbufenbuf, n):
                port = int(fbufenbuf_match[1] or "0")
                i = int(fbufenbuf_match[2])
                raw_fbufenbufs[port] = raw_fbufenbufs.get(port) or {}
                raw_fbufenbufs[port][i] = instance
            elif floatbuf_match := re.search(r.floatbuf, n):
                byte, port, bit = (int(floatbuf_match[1]), int(floatbuf_match[2] or "0"), int(floatbuf_match[3]))
                raw_floatbufs[port] = raw_floatbufs.get(port) or {}
                raw_floatbufs[port][byte] = raw_floatbufs[port].get(byte) or {}
                raw_floatbufs[port][byte][bit] = instance
            elif dobuf_match := re.search(r.dobuf, n):
                port = int(dobuf_match[1] or "0")
                i = int(dobuf_match[2])
                raw_dobufs[port] = raw_dobufs.get(port) or {}
                raw_dobufs[port][i] = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.slices = d2a({k: Slice(v) for k, v in raw_slices.items()})

        self.decoder_ands = d2a({k: d2a(v) for k, v in raw_decoder_ands.items()})

        self.enbufs = d2a(raw_enbufs)
        self.dibufs = d2a(raw_dibufs)
        self.dobufs = d2a({k: d2a(v) for k, v in raw_dobufs.items()})

        self.webufs = d2a(raw_webufs)
        self.abufs = d2a({k: d2a(v) for k, v in raw_abufs.items()})

        self.fbufenbufs = d2a({k: d2a(v) for k, v in raw_fbufenbufs.items()})

        self.ties = d2a({k: d2a(v) for k, v in raw_ties.items()})
        self.floatbufs = d2a({k: d2a({k: d2a(v2) for k, v2 in v.items()}) for k, v in raw_floatbufs.items()})

    def represent(self, tab_level: int = -1, file: TextIO = sys.stderr):
        tab_level += 1

        def ra(n, a, **kwargs):
            P.ra(n, a, tab_level, file, **kwargs)

        P.ri("Clock Buffer", self.clkbuf, tab_level, file)

        ra("Enable Buffers", self.enbufs)
        ra("Decoder AND Gates", self.decoder_ands, header="Address")
        ra("Write Enable Buffers", self.webufs)
        ra("Address Buffers", self.abufs, header="Address")
        ra("Data Input Buffers", self.dibufs)
        ra("Data Output Buffers", self.dobufs, header="Address")
        ra("Ties", self.ties, header="Address")
        ra("Float Buffer Enable Buffers", self.fbufenbufs, header="Address")
        ra("Float Buffers", self.floatbufs, header="Address")
        ra("Slices", self.slices, header="Slice")

    def place(self, row_list: List[Row], start_row: int = 0):
        # Prologue. Split vertical elements into left and right columns
        addresses = len(self.abufs)
        common = [self.clkbuf] + self.webufs
        chunks = []
        per_chunk = math.ceil(len(common) / addresses)
        i = 0

        while i < len(common):
            chunks.append(common[i: i + per_chunk])
            i += per_chunk

        vertical_left = []
        vertical_right = []
        right = True

        for i in range(0, len(self.abufs)):
            target = vertical_right if right else vertical_left
            target.append([
                self.enbufs[i],
                *self.abufs[i],
                *self.decoder_ands[i],
                *self.fbufenbufs[i]
            ] + chunks[i])
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
        current_row = start_row

        r = row_list[current_row]

        for dibuf in self.dibufs:
            r.place(dibuf)

        current_row += 1

        for slice in self.slices:
            current_row = slice.place(row_list, current_row)

        for i, port in enumerate(self.ties):
            r = row_list[current_row]
            for j, tie in enumerate(port):
                r.place(tie)
                for floatbuf in self.floatbufs[i][j]:
                    r.place(floatbuf)
            current_row += 1

        for port in self.dobufs:
            r = row_list[current_row]
            for dobuf in port:
                r.place(dobuf)
            current_row += 1

        Row.fill_rows(row_list, start_row, current_row)

        final_rows.append(current_row)

        # Act 3. Place Right Vertical Elements
        current_row = start_row
        
        for column in vertical_right:
            current_row = start_row
            for el in column:
                r = row_list[current_row]
                r.place(el)
                current_row += 1

        final_rows.append(current_row)

        # Epilogue 
        max_row = max(*final_rows)
        Row.fill_rows(row_list, start_row, max_row)
        return max_row

    def word_count(self):
        return 32

class Mux(Placeable):
    """
    Constraint: The number of selection buffers is necessarily == the number of bytes.
    """
    def __init__(self, instances: List[Instance]):
        # First access is the byte
        self.selbufs: List[List[Instance]] = None
        self.muxes: List[List[Instance]] = None

        raw_selbufs: Dict[int, Dict[int, Instance]] = {}
        raw_muxes: Dict[int, Dict[int, Instance]] = {}

        r = self.regexes()
        for instance in instances:
            n = instance.getName()
            if selbuf_match := re.search(r.selbuf, n):
                line, byte = (int(selbuf_match[1] or "0"), int(selbuf_match[2]))
                raw_selbufs[byte] = raw_selbufs.get(byte) or {}
                raw_selbufs[byte][line] = instance
            elif mux_match := re.search(r.mux, n):
                byte, bit = (int(mux_match[1]), int(mux_match[2]))
                raw_muxes[byte] = raw_muxes.get(byte) or {}
                raw_muxes[byte][bit] = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.selbufs = d2a({k: d2a(v) for k, v in raw_selbufs.items()})
        self.muxes = d2a({k: d2a(v) for k, v in raw_muxes.items()})

    def represent(self, tab_level: int = -1, file: TextIO = sys.stderr):
        tab_level += 1

        P.ra("Selection Buffers", self.selbufs, tab_level, file, header="Byte")
        P.ra("Logic Elements", self.muxes, tab_level, file, header="Byte")

    def place(self, row_list: List[Row], start_row: int = 0):
        r = row_list[start_row]

        for selbuf_lines, mux_bits in zip(self.selbufs, self.muxes):
            for line in selbuf_lines:
                r.place(line)
            for bit in mux_bits:
                r.place(bit)

        return start_row + 1


class HigherLevelPlaceable(Placeable):
    # TODO: Dual ported higher level placeables.
    def __init__(self, inner_re: RegExp, instances: List[Instance]):
        self.clkbuf: Instance = None
        self.enbuf: Instance = None
        self.blocks: List[Union[Block, HigherLevelPlaceable]] = None
        self.dibufs: List[Instance] = None
        self.webufs: List[Instance] = None
        self.abufs: List[Instance] = None
        self.domux: Mux = None

        raw_blocks: Dict[int, List[Instance]] = {}
        raw_decoder_ands: Dict[int, Instance] = {}

        raw_dibufs: Dict[int, Instance] = {}
        raw_webufs: Dict[int, Instance] = {}
        raw_abufs: Dict[int, Instance] = {}

        raw_domux: List[Instance] = []

        r_block = inner_re
        r = self.regexes()
        for instance in instances:
            n = instance.getName()
            if block_match := re.search(r_block, n):
                i = int(block_match[1])
                raw_blocks[i] = raw_blocks.get(i) or []
                raw_blocks[i].append(instance)
            elif decoder_and_match := re.search(r.decoder_and, n):
                i = int(decoder_and_match[1])
                raw_decoder_ands[i] = instance
            elif dibuf_match := re.search(r.dibuf, n):
                i = int(dibuf_match[1])
                raw_dibufs[i] = instance
            elif webuf_match := re.search(r.webuf, n):
                i = int(webuf_match[1])
                raw_webufs[i] = instance
            elif clkbuf_match := re.search(r.clkbuf, n):
                self.clkbuf = instance
            elif abuf_match := re.search(r.abuf, n):
                i = int(abuf_match[1])
                raw_abufs[i] = instance
            elif enbuf_match := re.search(r.enbuf, n):
                self.enbuf = instance
            elif domux_match := re.search(r.domux, n):
                raw_domux.append(instance)
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))
        self.blocks = d2a({k: constructor[inner_re](v) for k, v in
            raw_blocks.items()})
        self.decoder_ands = d2a(raw_decoder_ands)
        self.dibufs = d2a(raw_dibufs)

        self.webufs = d2a(raw_webufs)
        self.abufs = d2a(raw_abufs)
        self.domux = Mux(raw_domux)

    def represent(self, tab_level: int = -1, file: TextIO = sys.stderr):
        tab_level += 1

        def ra(n, a, **kwargs):
            P.ra(n, a, tab_level, file, **kwargs)

        if self.enbuf:
            P.ri("Enable Buffer", self.enbuf, tab_level, file)

        if self.clkbuf:
            P.ri("Clock Buffer", self.clkbuf, tab_level, file)

        if self.decoder_ands:
            ra("Decoder AND Gates", self.decoder_ands)

        if self.webufs:
            ra("Write Enable Buffers", self.webufs)

        if self.abufs:
            ra("Address Buffers", self.abufs)

        if self.dibufs:
            ra("Input Buffers", self.dibufs)

        ra("Blocks", self.blocks, header="Block")

        self.domux.represent(tab_level, file)

    def place(self, row_list: List[Row], start_row: int = 0):

        def symmetrically_placeable(obj):
            symm_placement_wc = 128
            return obj.word_count() > symm_placement_wc

        current_row = start_row
        r = row_list[current_row]

        for dibuf in self.dibufs:
            r.place(dibuf)

        current_row += 1

        # all of the big designs include 4 instances
        # of the smaller block they are constituted of
        # so they can all be 1:1 if they are 4x4
        # the smallest 1:1 is the 128 word block
        # it is placed all on top of each other
        partition_cap = int(math.sqrt(len(self.blocks)))
        if symmetrically_placeable(self):
            for block_idx in range(len(self.blocks)):
                if block_idx == partition_cap:
                    current_row = start_row
                current_row = self.blocks[block_idx].place(row_list, current_row)
        else:
            for ablock in self.blocks:
                current_row = ablock.place(row_list, current_row)

        current_row += 1

        current_row = self.domux.place(row_list, current_row)

        Row.fill_rows(row_list, start_row, current_row)

        last_column = [
            self.clkbuf,
            self.enbuf,
            *self.webufs,
            *self.abufs,
            *self.decoder_ands
        ]

        c2 = start_row
        for el in last_column:
            if el:
                r = row_list[c2]
                r.place(el)
                c2 += 1

        Row.fill_rows(row_list, start_row, current_row)


        return current_row

    def word_count(self):
        return len(self.blocks) * (self.blocks[0].word_count())

constructor = {
    r"\bBANK_B(\d+)\b": Block,
    r"\bBANK128_B(\d+)\b": partial(HigherLevelPlaceable, r"\bBANK_B(\d+)\b"),
    r"\bBANK512_B(\d+)\b": partial(HigherLevelPlaceable, r"\bBANK128_B(\d+)\b")
}
