from .util import eprint, d2a
from .row import Row

from opendbpy import dbInst
Instance = dbInst

import re
import sys
import math

# --
def RepresentInstance(instance):
    return "[I<%s> '%s']" % (instance.getMaster().getName(), instance.getName())

class Placeable(object):
    def place(self, row_list, current_row=0):
        raise Exception("Method unimplemented.")

    def represent(self, tab_level=-1, file=sys.stderr):
        raise Exception("Method unimplemented.")

class DataError(Exception):
    pass
# --

class Bit(Placeable):
    def __init__(self, instances):
        self.store = None
        self.obuf = None

        latch = r"\bLATCH\b"
        ff = r"\bFF\b"
        obuf = r"\bOBUF\b"

        for instance in instances:
            n = instance.getName()

            if ff_match := re.search(ff, n):
                self.store = instance
            elif obuf_match := re.search(obuf, n):
                self.obuf = instance
            elif latch_match := re.search(latch, n):
                self.store = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

    def represent(self, tab_level=-1, file=sys.stderr):
        tab_level += 1

        print("%sStorage Element %s" % ("".join(["  "] * tab_level), RepresentInstance(self.store)), file=file)
        print("%sOutput Buffer %s" % ("".join(["  "] * tab_level), RepresentInstance(self.obuf)), file=file)

    def place(self, row_list, start_row=0):
        r = row_list[start_row]

        r.place(self.store)
        r.place(self.obuf)

        return start_row

class Byte(Placeable):
    def __init__(self, instances):
        self.clockgate = None
        self.cgand = None
        self.selinv = None
        self.clkinv = None
        raw_bits = {}

        bit = r"\BIT\\\[(\d+)\\\]"
        cg = r"\bCG\b"
        cgand = r"\bCGAND\b"
        selinv = r"\bSELINV\b"
        clkinv = r"\bCLKINV\b"

        for instance in instances:
            n = instance.getName()

            if bit_match := re.search(bit, n):
                i = int(bit_match[1])
                raw_bits[i] = raw_bits.get(i) or []
                raw_bits[i].append(instance)
            elif cg_match := re.search(cg, n):
                self.clockgate = instance
            elif cgand_match := re.search(cgand, n):
                self.cgand = instance
            elif selinv_match := re.search(selinv, n):
                self.selinv = instance
            elif clkinv_match := re.search(clkinv, n):
                self.clkinv = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.bits = d2a({k: Bit(v) for k, v in raw_bits.items()})

    def represent(self, tab_level=-1, file=sys.stderr):
        tab_level += 1

        print("%sClock Gate %s" % ("".join(["  "] * tab_level), RepresentInstance(self.clockgate)), file=file)
        print("%sClock Gate AND%s" % ("".join(["  "] * tab_level), RepresentInstance(self.cgand)), file=file)
        print("%sSelect Line Inverter%s" % ("".join(["  "] * tab_level), RepresentInstance(self.selinv)), file=file)
        if self.clkinv is not None:
            print("%sClock Inverter%s" % ("".join(["  "] * tab_level), RepresentInstance(self.clkinv)), file=file)

        print("%sBits" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for i, bit in enumerate(self.bits):
            print("%sBit %i" % ("".join(["  "] * tab_level), i), file=file)
            bit.represent(tab_level=tab_level, file=file)
        tab_level -= 1

    def place(self, row_list, start_row=0):
        r = row_list[start_row]

        for bit in self.bits:
            bit.place(row_list, start_row)

        r.place(self.clockgate)
        r.place(self.cgand)
        r.place(self.selinv)
        if self.clkinv is not None:
            r.place(self.clkinv)

        return start_row

class Word(Placeable):
    def __init__(self, instances):
        self.clkbuf = None
        self.selbuf = None
        raw_bytes = {}

        clkbuf = r"\bCLKBUF\b"
        selbuf = r"\bSELBUF\b"
        byte = r"\bB(\d+)\b"

        for instance in instances:
            n = instance.getName()

            if byte_match := re.search(byte, n):
                i = int(byte_match[1])
                raw_bytes[i] = raw_bytes.get(i) or []
                raw_bytes[i].append(instance)
            elif sb_match := re.search(selbuf, n):
                self.selbuf = instance
            elif cb_match := re.search(clkbuf, n):
                self.clkbuf = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.bytes = d2a({k: Byte(v) for k, v in raw_bytes.items()})

    def represent(self, tab_level=-1, file=sys.stderr):
        tab_level += 1

        print("%sClock Buffer %s" % ("".join(["  "] * tab_level), RepresentInstance(self.clkbuf)), file=file)
        print("%sSelect Line Buffer %s" % ("".join(["  "] * tab_level), RepresentInstance(self.selbuf)), file=file)

        print("%sBytes" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for i, byte in enumerate(self.bytes):
            print("%sByte %i" % ("".join(["  "] * tab_level), i), file=file)
            byte.represent(tab_level=tab_level, file=file)
        tab_level -= 1

    def place(self, row_list, start_row=0):
        r = row_list[start_row]

        for byte in self.bytes:
            byte.place(row_list, start_row)

        r.place(self.clkbuf)
        r.place(self.selbuf)

        return start_row

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

        self.and_gates = d2a(raw_and_gates)
        self.abufs = d2a(raw_abufs)

    def represent(self, tab_level=-1, file=sys.stderr):
        tab_level += 1

        print("%sEnable Buffer %s" % ("".join(["  "] * tab_level), RepresentInstance(self.enbuf)), file=file)

        print("%sAND Gates" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for instance in self.and_gates:
            print("%s%s" % ("".join(["  "] * tab_level), RepresentInstance(instance)), file=file)
        tab_level -= 1

        print("%sAddress Buffers" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for instance in self.abufs:
            print("%s%s" % ("".join(["  "] * tab_level), RepresentInstance(instance)), file=file)
        tab_level -= 1

        tab_level -= 1

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

class Slice(Placeable): # A slice is defined as 8 words.
    def __init__(self, instances):
        raw_words = {}
        self.decoder = None
        self.webufs = []
        self.clkbuf = None

        word = r"\bWORD\\\[(\d+)\\\]"
        webuf = r"\bWEBUF\b"
        clkbuf = r"\bCLKBUF\b"
        decoder = r"\bDEC\b"

        decoder_instances = []

        for instance in instances:
            n = instance.getName()

            if word_match := re.search(word, n):
                i = int(word_match[1])
                raw_words[i] = raw_words.get(i) or []
                raw_words[i].append(instance)
            elif d_match := re.search(decoder, n):
                decoder_instances.append(instance)
            elif wb_match := re.search(webuf, n):
                self.webufs.append(instance)
            elif cb_match := re.search(clkbuf, n):
                self.clkbuf = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.decoder = Decoder3x8(decoder_instances)

        self.words = d2a({k: Word(v) for k, v in raw_words.items()})

        word_count = len(self.words)
        if word_count != 8:
            raise DataError("Slice has (%i/8) words." % word_count)

    def represent(self, tab_level=-1, file=sys.stderr):
        tab_level += 1

        print("%sDecoder" % "".join(["  "] * tab_level), file=file)
        self.decoder.represent(tab_level=tab_level, file=file)

        print("%sWrite Enable Buffers" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for instance in self.webufs:
            print("%s%s" % ("".join(["  "] * tab_level), RepresentInstance(instance)), file=file)
        tab_level -= 1

        print("%sWords" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for i, word in enumerate(self.words):
            print("%sWord %i" % ("".join(["  "] * tab_level), i), file=file)
            word.represent(tab_level=tab_level, file=file)
        tab_level -= 1

    def place(self, row_list, start_row=0):
        current_row = start_row

        for word in self.words:
            word.place(row_list, current_row)
            current_row += 1

        Row.fill_rows(row_list, start_row, current_row)

        last_column = [self.webufs[0], self.webufs[1], self.webufs[2], self.webufs[3], self.clkbuf, None, None, None]

        for i in range(8):
            r = row_list[start_row + i]
            if last_column[i] is not None:
                r.place(last_column[i])

        Row.fill_rows(row_list, start_row, current_row)

        self.decoder.place(row_list, start_row)

        Row.fill_rows(row_list, start_row, current_row)

        return current_row

class Block(Placeable): # A block is defined as 4 slices (32 words).
    def __init__(self, instances):
        self.clkbuf = None
        self.enbuf = None

        raw_slices = {}
        raw_decoder_ands = {}

        raw_dibufs = {}
        raw_dobufs = {}

        raw_webufs = {}

        raw_abufs = {}

        raw_ties = {}
        raw_fbufenbufs = {}
        raw_floatbufs = {}

        slice = r"\SLICE\\\[(\d+)\\\]"
        decoder_and = r"\bDEC\.AND(\d+)\b"

        dibuf = r"\bDIBUF\\\[(\d+)\\\]"
        dobuf = r"\bDo_FF\\\[(\d+)\\\]"

        webuf = r"\bWEBUF\\\[(\d+)\\\]"
        clkbuf = r"\bCLKBUF\b"

        abuf = r"\bABUF\\\[(\d+)\\\]"
        enbuf = r"\bENBUF\b"

        tie = r"\bTIE\\\[(\d+)\\\]"
        fbufenbuf = r"\bFBUFENBUF\\\[(\d+)\\\]"
        floatbuf = r"\bFLOATBUF_B(\d+)\\\[(\d+)\\\]"

        for instance in instances:
            n = instance.getName()

            if slice_match := re.search(slice, n):
                i = int(slice_match[1])
                raw_slices[i] = raw_slices.get(i) or []
                raw_slices[i].append(instance)
            elif decoder_and_match := re.search(decoder_and, n):
                i = int(decoder_and_match[1])
                raw_decoder_ands[i] = instance
            elif dibuf_match := re.search(dibuf, n):
                i = int(dibuf_match[1])
                raw_dibufs[i] = instance
            elif webuf_match := re.search(webuf, n):
                i = int(webuf_match[1])
                raw_webufs[i] = instance
            elif clkbuf_match := re.search(clkbuf, n):
                self.clkbuf = instance
            elif abuf_match := re.search(abuf, n):
                i = int(abuf_match[1])
                raw_abufs[i] = instance
            elif enbuf_match := re.search(enbuf, n):
                self.enbuf = instance
            elif tie_match := re.search(tie, n):
                i = int(tie_match[1])
                raw_ties[i] = instance
            elif fbufenbuf_match := re.search(fbufenbuf, n):
                i = int(fbufenbuf_match[1])
                raw_fbufenbufs[i] = instance
            elif floatbuf_match := re.search(floatbuf, n):
                byte, bit = (floatbuf_match[1], floatbuf_match[2])
                raw_floatbufs[byte] = raw_floatbufs.get(byte) or {}
                raw_floatbufs[byte][bit] = instance
            elif dobuf_match := re.search(dobuf, n):
                i = int(dobuf_match[1])
                raw_dobufs[i] = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.slices = d2a({k: Slice(v) for k, v in raw_slices.items()})

        self.decoder_ands = d2a(raw_decoder_ands)

        self.dibufs = d2a(raw_dibufs)
        self.dobufs = d2a(raw_dobufs)

        self.webufs = d2a(raw_webufs)
        self.abufs = d2a(raw_abufs)
        self.ties = d2a(raw_ties)
        self.fbufenbufs = d2a(raw_fbufenbufs)
        self.floatbufs = d2a({k: d2a(v) for k, v in raw_floatbufs.items()})

    def represent(self, tab_level=-1, file=sys.stderr):
        tab_level += 1

        print("%sEnable Buffer %s" % ("".join(["  "] * tab_level), RepresentInstance(self.enbuf)), file=file)

        print("%sClock Buffer %s" % ("".join(["  "] * tab_level), RepresentInstance(self.clkbuf)), file=file)

        print("%sDecoder AND Gates" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for instance in self.decoder_ands:
            print("%s%s" % ("".join(["  "] * tab_level), RepresentInstance(instance)), file=file)
        tab_level -= 1

        print("%sWrite Enable Buffers" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for instance in self.webufs:
            print("%s%s" % ("".join(["  "] * tab_level), RepresentInstance(instance)), file=file)
        tab_level -= 1

        print("%sAddress Buffers" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for instance in self.abufs:
            print("%s%s" % ("".join(["  "] * tab_level), RepresentInstance(instance)), file=file)
        tab_level -= 1

        print("%sTies" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for instance in self.ties:
            print("%s%s" % ("".join(["  "] * tab_level), RepresentInstance(instance)), file=file)
        tab_level -= 1

        print("%sFloatbuf Enable Buffers" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for instance in self.fbufenbufs:
            print("%s%s" % ("".join(["  "] * tab_level), RepresentInstance(instance)), file=file)
        tab_level -= 1

        print("%sInput Buffers" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for instance in self.dibufs:
            print("%s%s" % ("".join(["  "] * tab_level), RepresentInstance(instance)), file=file)
        tab_level -= 1

        print("%sOutput Buffers" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for instance in self.dobufs:
            print("%s%s" % ("".join(["  "] * tab_level), RepresentInstance(instance)), file=file)
        tab_level -= 1

        print("%sFloat Buffers" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for i, group in enumerate(self.floatbufs):
            print("%sGroup %i" % ("".join(["  "] * tab_level), i), file=file)
            tab_level += 1
            for instance in group:
                print("%s%s" % ("".join(["  "] * tab_level), RepresentInstance(instance)), file=file)
            tab_level -= 1
        tab_level -= 1

        print("%sSlices" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for i, slice in enumerate(self.slices):
            print("%sSlice %i" % ("".join(["  "] * tab_level), i), file=file)
            slice.represent(tab_level=tab_level, file=file)
        tab_level -= 1

    def place(self, row_list, start_row=0):
        current_row = start_row
        r = row_list[current_row]

        for dibuf in self.dibufs:
            r.place(dibuf)

        current_row += 1

        for slice in self.slices:
            current_row = slice.place(row_list, current_row)

        r = row_list[current_row]
        for i, tie in enumerate(self.ties):
            r.place(tie)
            for floatbuf in self.floatbufs[i]:
                r.place(floatbuf)

        current_row += 1

        r = row_list[current_row]
        for dobuf in self.dobufs:
            r.place(dobuf)

        current_row += 1

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
            r = row_list[c2]
            r.place(el)
            c2 += 1

        c3 = current_row - 1
        for el in reversed(self.fbufenbufs):
            r = row_list[c3]
            r.place(el)
            c3 -= 1

        Row.fill_rows(row_list, start_row, current_row)

        return current_row

class Mux(Placeable): # Pretty generic, only constraint is the number of selbufs must be == the number of bytes
    def __init__(self, instances):
        raw_selbufs = {}
        raw_muxes = {}

        selbuf = r"\bSEL(\d*)?BUF\\\[(\d+)\\\]"
        mux = r"\bMUX(\d+)\\\[(\d+)\\\]" 

        for instance in instances:
            n = instance.getName()
            if selbuf_match := re.search(selbuf, n):
                line, byte = (int(selbuf_match[1] or "0"), int(selbuf_match[2]))
                raw_selbufs[byte] = raw_selbufs.get(byte) or {}
                raw_selbufs[byte][line] = instance
            elif mux_match := re.search(mux, n):
                byte, bit = (int(mux_match[1]), int(mux_match[2]))
                raw_muxes[byte] = raw_muxes.get(byte) or {}
                raw_muxes[byte][bit] = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.selbufs = d2a({k: d2a(v) for k, v in raw_selbufs.items()})
        self.muxes = d2a({k: d2a(v) for k, v in raw_muxes.items()})
    
    def represent(self, tab_level=-1, file=sys.stderr):
        tab_level += 1

        # TODO

    def place(self, row_list, start_row=0):
        r = row_list[start_row]
        
        for selbuf_lines, mux_bits in zip(self.selbufs, self.muxes):
            for line in selbuf_lines:
                r.place(line)
            for bit in mux_bits:
                r.place(bit)

        return start_row + 1

class HigherLevelPlaceable(Placeable):
    def __init__(self, instances):
        # TODO: Generalize beyond Block
        self.clkbuf = None
        self.enbuf = None
        raw_blocks = {}
        raw_decoder_ands = {}

        raw_dibufs = {}
        raw_webufs = {}
        raw_abufs = {}

        raw_domux = []

        clkbuf = r"\bCLKBUF\b"
        enbuf = r"\bENBUF\b"

        block = r"\bBANK_B(\d+)\b"
        decoder_and = r"\bDEC\.AND(\d+)\b"
        dibuf = r"\bDIBUF\\\[(\d+)\\\]"
        domux = r"\bDoMUX\b"
        webuf = r"\bWEBUF\\\[(\d+)\\\]"
        abuf = r"\bABUF\\\[(\d+)\\\]"

        for instance in instances:
            n = instance.getName()
            if block_match := re.search(block, n):
                i = int(block_match[1])
                raw_blocks[i] = raw_blocks.get(i) or []
                raw_blocks[i].append(instance)
            elif decoder_and_match := re.search(decoder_and, n):
                i = int(decoder_and_match[1])
                raw_decoder_ands[i] = instance
            elif dibuf_match := re.search(dibuf, n):
                i = int(dibuf_match[1])
                raw_dibufs[i] = instance
            elif webuf_match := re.search(webuf, n):
                i = int(webuf_match[1])
                raw_webufs[i] = instance
            elif clkbuf_match := re.search(clkbuf, n):
                self.clkbuf = instance
            elif abuf_match := re.search(abuf, n):
                i = int(abuf_match[1])
                raw_abufs[i] = instance
            elif enbuf_match := re.search(enbuf, n):
                self.enbuf = instance
            elif domux_match := re.search(domux, n):
                raw_domux.append(instance)
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))
        self.blocks = d2a({k: Block(v) for k, v in
            raw_blocks.items()})
        self.decoder_ands = d2a(raw_decoder_ands)
        self.dibufs = d2a(raw_dibufs)

        self.webufs = d2a(raw_webufs)
        self.abufs = d2a(raw_abufs)
        self.domux = Mux(raw_domux)

    def represent(self, tab_level=-1, file=sys.stderr):
        tab_level += 1

        print("%sEnable Buffer %s" % ("".join(["  "] * tab_level), RepresentInstance(self.enbuf)), file=file)

        print("%sClock Buffer %s" % ("".join(["  "] * tab_level), RepresentInstance(self.clkbuf)), file=file)

        print("%sDecoder AND Gates" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for instance in self.decoder_ands:
            print("%s%s" % ("".join(["  "] * tab_level), RepresentInstance(instance)), file=file)
        tab_level -= 1

        print("%sWrite Enable Buffers" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for instance in self.webufs:
            print("%s%s" % ("".join(["  "] * tab_level), RepresentInstance(instance)), file=file)
        tab_level -= 1

        print("%sAddress Buffers" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for instance in self.abufs:
            print("%s%s" % ("".join(["  "] * tab_level), RepresentInstance(instance)), file=file)
        tab_level -= 1

        print("%sInput Buffers" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for instance in self.dibufs:
            print("%s%s" % ("".join(["  "] * tab_level), RepresentInstance(instance)), file=file)
        tab_level -= 1

        print("%sBlocks" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for i, ablock in enumerate(self.blocks):
            print("%sBlock %i" % ("".join(["  "] * tab_level), i), file=file)
            ablock.represent(tab_level=tab_level, file=file)
        tab_level -= 1

        # TODO: Mux
        tab_level -= 1

    def place(self, row_list, start_row=0):
        current_row = start_row
        r = row_list[current_row]

        for dibuf in self.dibufs:
            r.place(dibuf)

        current_row += 1

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
            r = row_list[c2]
            r.place(el)
            c2 += 1

        Row.fill_rows(row_list, start_row, current_row)


        return current_row
