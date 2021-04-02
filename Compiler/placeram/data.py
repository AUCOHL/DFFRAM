from .util import eprint

import re
import sys
import math

class DataError(Exception):
    pass

class Row(object):
    sw = None
    sh = None
    
    create_tap = None
    tap_distance = None

    create_fill = None 

    # Assumptions:
    #   All fills are powers of 2.
    #   If fill 2^n is available, then for 0 <= i < n: 2^i is available.
    supported_fill_sizes = None

    max_fill_size = None

    def __init__(self, ordinal, row_obj):
        self.ordinal = ordinal
        self.obj = row_obj

        self.origin = self.obj.getOrigin()
        [self.x, self.y] = self.obj.getOrigin()
        self.max = self.obj.getBBox().xMax()

        self.orientation = self.obj.getOrient()

        self.cell_counter = 0
        self.tap_counter = 0
        self.fill_counter = 0
        self.since_last_tap = 0 if self.ordinal % 2 == 0 else Row.tap_distance / 2

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
        eprint("Found %i rows…" % len(rows))

        Row.create_tap = create_tap
        Row.sw, Row.sh = (regular_site.getWidth(), regular_site.getHeight())
        Row.tap_distance = max_tap_distance

        Row.create_fill = create_fill
        Row.supported_fill_sizes = supported_fill_sizes
        Row.max_fill_size = max(supported_fill_sizes)

        rows.reverse()
        returnable = []
        for i, row in enumerate(rows):
            returnable.append(Row(i, row))
        return returnable

    @staticmethod
    def fill_rows(rows, from_index, to_index):
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
        def bin_pack(remaining, max_fill_size):
            fills = []
            while remaining > max_fill_size:
                fills.append(max_fill_size)
                remaining -= max_fill_size

            # I'm using nature's bin-packing algorithm for base-2.
            # Binary representation.
            current_size = 1
            while remaining > 0:
                if remaining & 1:
                    fills.append(current_size)
                remaining >>= 1
                current_size <<= 1

            return fills
        max_sw = -1
        for i in range(from_index, to_index + 1):
            r = rows[i]
            width = r.x
            width_sites = int(width / Row.sw)
            max_sw = max(max_sw, width_sites)

        eprint("Padding to %i sites…" % max_sw)
            
        for i in range(from_index, to_index + 1):
            r = rows[i]
            width = r.x
            width_sites = int(width / Row.sw)

            empty = max_sw - width_sites

            remaining = empty

            fills = bin_pack(empty, Row.max_fill_size)
            
            for fill in fills:
                fill_cell = Row.create_fill("fill_%i_%i" % (i, r.fill_counter), fill)
                r.place(fill_cell, ignore_tap=True)
                r.fill_counter += 1


def RepresentInstance(instance):
    return "[I<%s> '%s']" % (instance.getMaster().getName(), instance.getName())

class Placeable(object):
    def place(self, row_list, current_row=0):
        raise Exception("Method unimplemented.")

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
            elif latch_match := res.search(latch, n):
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
        rbits = {}

        bit = r"\BIT\\\[(\d+)\\\]"
        cg = r"\bCG\b"
        cgand = r"\bCGAND\b"
        selinv = r"\bSELINV\b"
        clkinv = r"\bCLKINV\b"

        for instance in instances:
            n = instance.getName()

            if bit_match := re.search(bit, n):
                i = int(bit_match[1])
                rbits[i] = rbits.get(i) or []
                rbits[i].append(instance)
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

        self.bits = {}
        for k, v in rbits.items():
            self.bits[k] = Bit(v)

    def represent(self, tab_level=-1, file=sys.stderr):
        tab_level += 1

        print("%sClock Gate %s" % ("".join(["  "] * tab_level), RepresentInstance(self.clockgate)), file=file)
        print("%sClock Gate AND%s" % ("".join(["  "] * tab_level), RepresentInstance(self.cgand)), file=file)
        print("%sSelect Line Inverter%s" % ("".join(["  "] * tab_level), RepresentInstance(self.selinv)), file=file)
        if self.clkinv is not None:
            print("%sClock Inverter%s" % ("".join(["  "] * tab_level), RepresentInstance(self.clkinv)), file=file)
        
        print("%sBits" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for (k, v) in self.bits.items():
            print("%sBit %i" % ("".join(["  "] * tab_level), k), file=file)
            v.represent(tab_level=tab_level)
        tab_level -= 1

    def place(self, row_list, start_row=0):
        r = row_list[start_row]

        bits_sorted = list(self.bits.items())
        bits_sorted.sort(reverse=True, key=lambda x: x[0])

        for k, v in bits_sorted:
            v.place(row_list, start_row)

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
        rbytes = {}

        clkbuf = r"\bCLKBUF\b"
        selbuf = r"\bSELBUF\b"
        byte = r"\bB(\d+)\b"

        for instance in instances:
            n = instance.getName()

            if cb_match := re.search(clkbuf, n):
                self.clkbuf = instance
            elif sb_match := re.search(selbuf, n):
                self.selbuf = instance
            elif byte_match := re.search(byte, n):
                i = int(byte_match[1])
                rbytes[i] = rbytes.get(i) or []
                rbytes[i].append(instance)
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.bytes = {}
        for k, v in rbytes.items():
            self.bytes[k] = Byte(v)

    def represent(self, tab_level=-1, file=sys.stderr):
        tab_level += 1

        print("%sClock Buffer %s" % ("".join(["  "] * tab_level), RepresentInstance(self.clkbuf)), file=file)
        print("%sSelect Line Buffer %s" % ("".join(["  "] * tab_level), RepresentInstance(self.selbuf)), file=file)

        print("%sBytes" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for (k, v) in self.bytes.items():
            print("%sByte %i" % ("".join(["  "] * tab_level), k), file=file)
            v.represent(tab_level=tab_level)
        tab_level -= 1

    def place(self, row_list, start_row=0):
        r = row_list[start_row]

        bytes_sorted = list(self.bytes.items())
        bytes_sorted.sort(reverse=True, key=lambda x: x[0])

        for k, v in bytes_sorted:
            v.place(row_list, start_row)
        
        r.place(self.clkbuf)
        r.place(self.selbuf)

        return start_row

class Decoder3x8(Placeable):
    def __init__(self, instances):
        self.and_gates = []
        self.abufs = []
        self.enbuf = None

        dand = r"\bAND(\d+)\b"
        abuf = r"\bABUF\\\[(\d+)\\\]"
        enbuf = r"\bENBUF\b"

        for instance in instances:
            n = instance.getName()

            if and_match := re.search(dand, n):
                and_number = int(and_match[1])
                self.and_gates.append((and_number, instance))
            elif abuf_match := re.search(abuf, n):
                abuf_number = int(abuf_match[1])
                self.abufs.append((abuf_number, instance))
            elif enbuf_match := re.search(enbuf, n):
                self.enbuf = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.and_gates.sort(key=lambda x: x[0])
        self.and_gates = list(map(lambda x: x[1], self.and_gates))

        self.abufs.sort(key=lambda x: x[0])
        self.abufs = list(map(lambda x: x[1], self.abufs))

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

        for i in range(start_row + 8):
            r = row_list[i]
            
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
            elif wb_match := re.search(webuf, n):
                self.webufs.append(instance)
            elif cb_match := re.search(clkbuf, n):
                self.clkbuf = instance
            elif d_match := re.search(decoder, n):
                decoder_instances.append(instance)
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.decoder = Decoder3x8(decoder_instances)

        self.words = {}
        for (k, v) in raw_words.items():
            self.words[k] = Word(v)

        word_count = len(self.words.keys())
        if word_count != 8:
            raise DataError("Slice has (%i/8) words." % word_count) 

    def represent(self, tab_level=-1, file=sys.stderr):
        tab_level += 1

        print("%sDecoder" % "".join(["  "] * tab_level), file=file)
        self.decoder.represent(tab_level=tab_level)

        print("%sWrite Enable Buffers" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for instance in self.webufs:
            print("%s%s" % ("".join(["  "] * tab_level), RepresentInstance(instance)), file=file)
        tab_level -= 1

        print("%sWords" % "".join(["  "] * tab_level), file=file)
        tab_level += 1
        for (k, v) in self.words.items():
            print("%sWord %i" % ("".join(["  "] * tab_level), k), file=file)
            v.represent(tab_level=tab_level)
        tab_level -= 1

    def place(self, row_list, start_row=0):
        current_row = start_row
        words_sorted = list(self.words.items())
        words_sorted.sort(reverse=True, key=lambda x: x[0])

        for _, word in words_sorted:
            word.place(row_list, current_row)
            current_row += 1

        Row.fill_rows(row_list, start_row, start_row + 7)

        last_column = [self.webufs[0], self.webufs[1], self.webufs[2], self.webufs[3], self.clkbuf, None, None, None]

        for i in range(start_row + 8):
            r = row_list[i]
            if last_column[i] is not None:
                r.place(last_column[i]) 

        Row.fill_rows(row_list, start_row, start_row + 7)

        self.decoder.place(row_list, start_row)       

        Row.fill_rows(row_list, start_row, start_row + 7)

        return current_row