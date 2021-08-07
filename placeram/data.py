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
from .util import d2a
from .row import Row
from .placeable import Placeable, DataError
from .common_data import *

from opendb import dbInst as Instance

import math
from typing import Callable, List, Dict, Union
from itertools import zip_longest

# --

P = Placeable
S = Placeable.Sieve

class Bit(Placeable):
    def __init__(self, instances: List[Instance]):
        self.sieve(instances, [
            S(variable="store"),
            S(variable="obufs", groups=["port"])
        ])

        self.dicts_to_lists()

    def place(self, row_list: List[Row], start_row: int = 0):
        r = row_list[start_row]

        r.place(self.store)
        for obuf in self.obufs:
            r.place(obuf)

        return start_row

class Byte(Placeable):
    def __init__(self, instances: List[Instance]):
        raw_bits: Dict[int, List[Instance]] = {}
        def process_bit(instance, bit):
            raw_bits[bit] = raw_bits.get(bit) or []
            raw_bits[bit].append(instance)

        self.sieve(instances, [
            S(variable="bits", groups=["bit"], custom_behavior=process_bit),
            S(variable="clockgate"),
            S(variable="cgand"),
            S(variable="clkinv"),
            S(variable="clkdiode"),
            S(variable="selinvs", groups=["line"]),
        ])

        self.dicts_to_lists()
        self.bits = d2a({k: Bit(v) for k, v in raw_bits.items()})

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
        raw_bytes: Dict[int, List[Instance]] = {}
        def process_byte(instance, byte):
            raw_bytes[byte] = raw_bytes.get(byte) or []
            raw_bytes[byte].append(instance)

        self.sieve(instances, [
            S(variable="bytes", groups=["byte"], custom_behavior=process_byte),
            S(variable="clkbuf"),
            S(variable="selbufs", groups=["port"])
        ])

        self.dicts_to_lists()
        self.bytes = d2a({k: Byte(v) for k, v in raw_bytes.items()})

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

class Slice(Placeable): # A slice is defined as 8 words.
    def __init__(self, instances: List[Instance]):
        raw_words: Dict[int, List[Instance]] = {}
        def process_word(instance, word):
            raw_words[word] = raw_words.get(word) or []
            raw_words[word].append(instance)

        raw_decoders: Dict[int, List[Instance]] = {}
        def process_decoder(instance, decoder):
            raw_decoders[decoder] = raw_decoders.get(decoder) or []
            raw_decoders[decoder].append(instance)

        self.sieve(instances, [
            S(variable="words", groups=["word"], custom_behavior=process_word),
            S(variable="decoders", groups=["port"], custom_behavior=process_decoder),
            S(variable="clkbuf"),
            S(variable="webufs", groups=["line"]),
        ])

        self.dicts_to_lists()

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
        common = list(filter(lambda x: x, common))
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
        raw_slices: Dict[int, List[Instance]] = {}
        def process_slice(instance, slice):
            raw_slices[slice] = raw_slices.get(slice) or []
            raw_slices[slice].append(instance)

        self.sieve(instances, [
            S(variable="slices", groups=["slice"], custom_behavior=process_slice),
            S(variable="clk_diode"),
            S(variable="clkbuf"),
            S(variable="webufs", groups=["bit"]),
            S(variable="enbufs", groups=["port"]),
            S(variable="a_diodes", groups=["port", "address_bit"]),
            S(variable="abufs", groups=["port", "address_bit"]),
            S(variable="decoder_ands", groups=["port", "bit"]),
            S(variable="dibufs", groups=["bit"]),
            S(variable="dobufs", groups=["port", "bit"]),
            S(variable="dobuf_diodes", groups=["port", "bit"]),
            S(variable="fbufenbufs", groups=["port", "bit"]),
            S(variable="ties", groups=["port", "bit"]),
            S(variable="floatbufs", groups=["port", "byte", "bit"], group_rx_order=[2, 1, 3])
        ])

        self.dicts_to_lists()

        self.slices = d2a({k: Slice(v) for k, v in raw_slices.items()})

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
        raw_blocks: Dict[int, List[Instance]] = {}
        def process_block(instance, block):
            raw_blocks[block] = raw_blocks.get(block) or []
            raw_blocks[block].append(instance)

        raw_domuxes: Dict[int, List[Instance]] = {}
        def process_raw_domuxes(instance, domux):
            raw_domuxes[domux] = raw_domuxes.get(domux) or []
            raw_domuxes[domux].append(instance)

        self.sieve(instances, [
            S(variable=f"block{block_size}", groups=["block"], custom_behavior=process_block),
            S(variable="domuxes", groups=["domux"], custom_behavior=process_raw_domuxes),
            S(variable="clk_diode"),
            S(variable="clkbuf"),
            S(variable="di_diodes", groups=["bit"]),
            S(variable="dibufs", groups=["bit"]),
            S(variable="webufs", groups=["bit"]),
            S(variable="enbufs", groups=["port"]),
            S(variable="decoder_ands", groups=["port", "bit"]),
            S(variable="abufs", groups=["port", "address_bit"]),
            S(variable="a_diodes", groups=["port", "address_bit"])
        ])

        self.dicts_to_lists()

        self.blocks = d2a({
            k: create_hierarchy(v, block_size) for k, v in  raw_blocks.items()
        })
        self.domuxes = d2a({ k: Mux(v) for k, v in raw_domuxes.items()})

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

            for diode, dibuf in zip_longest(self.di_diodes, self.dibufs):
                if diode is not None:
                    r.place(diode)
                r.place(dibuf)

            current_row += 1

            partition_cap = int(math.sqrt(len(self.blocks)))
            if symmetrically_placeable():
                max_rows = []
                for i in range(len(self.blocks)):
                    if i == partition_cap:
                        current_row = start_row
                    current_row = self.blocks[i].place(row_list, current_row)
                    max_rows.append(current_row)
                current_row = max(max_rows)
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
                *([self.clkbuf, self.clk_diode] if self.clkbuf is not None else []),
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