from .util import eprint

import re
import math

class DataError(Exception):
    pass

class Row(object):
    sw = None
    sh = None
    
    tap_distance = None

    create_tap = None

    def __init__(self, ordinal, row_obj):
        self.ordinal = ordinal
        self.obj = row_obj

        self.origin = self.obj.getOrigin()
        [self.x, self.y] = self.obj.getOrigin()
        self.max = self.obj.getBBox().xMax()

        self.orientation = self.obj.getOrient()

        self.cell_counter = 0
        self.tap_counter = 0
        self.since_last_tap = 0 if self.ordinal % 2 == 0 else Row.tap_distance / 2

    def tap(self, width=0):
        location = self.x

        if self.since_last_tap + width > Row.tap_distance:
            self.place(Row.create_tap("tap_%i_%i" % (self.ordinal, self.tap_counter)), placing_tap=True)
            self.tap_counter += 1
            self.since_last_tap = 0
        else:
            self.since_last_tap += width

    def place(self, instance, placing_tap=False):
        width = instance.getMaster().getWidth()
        if not placing_tap:
            self.tap(width)

        instance.setOrient(self.orientation)
        instance.setLocation(self.x, self.y)
        instance.setPlacementStatus("PLACED")

        self.x += width
        self.cell_counter += 1

    @staticmethod
    def from_odb(rows, regular_site, create_tap, max_tap_distance=-1):
        eprint("Found %i rows…" % len(rows))

        Row.create_tap = create_tap
        Row.sw, Row.sh = (regular_site.getWidth(), regular_site.getHeight())
        Row.tap_distance = max_tap_distance

        rows.reverse()
        returnable = []
        for i, row in enumerate(rows):
            returnable.append(Row(i, row))
        return returnable

def RepresentInstance(instance):
    return "[I<%s> '%s']" % (instance.getMaster().getName(), instance.getName())

class Placeable(object):
    def place(self, row_list, current_row=0):
        raise Exception("Method unimplemented.")

class Bit(Placeable):
    def __init__(self, instances):
        self.store = None
        self.obuf = None

        ff = r"\bFF\b"
        obuf = r"\bOBUF\b"

        for instance in instances:
            n = instance.getName()

            if ff_match := re.search(ff, n):
                self.store = instance
            elif obuf_match := re.search(obuf, n):
                self.obuf = instance
            else:
                raise DataError("Unknown element in bit: %s" % n)
    
    def represent(self, tab_level=-1):
        tab_level += 1

        eprint("%sStorage Element %s" % ("".join(["  "] * tab_level), RepresentInstance(self.store)))
        eprint("%sOutput Buffer %s" % ("".join(["  "] * tab_level), RepresentInstance(self.obuf)))

    def place(self, row_list, start_row=0):
        r = row_list[start_row]

        r.place(self.store)
        r.place(self.obuf)

        return start_row

class Byte(Placeable): 
    def __init__(self, instances):
        self.clockgate = None
        self.cgand = None
        self.inv = None
        rbits = {}

        bit = r"\BIT\\\[(\d+)\\\]"
        cg = r"\bCG\b"
        cgand = r"\bCGAND\b"
        inv = r"\bINV\b"

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
            elif inv_match := re.search(inv, n):
                self.inv = instance

        self.bits = {}
        for k, v in rbits.items():
            self.bits[k] = Bit(v)

    def represent(self, tab_level=-1):
        tab_level += 1

        eprint("%sClock Gate %s" % ("".join(["  "] * tab_level), RepresentInstance(self.clockgate)))
        eprint("%sClock Gate AND%s" % ("".join(["  "] * tab_level), RepresentInstance(self.cgand)))
        eprint("%sInverter%s" % ("".join(["  "] * tab_level), RepresentInstance(self.inv)))
        
        eprint("%sBits" % "".join(["  "] * tab_level))
        tab_level += 1
        for (k, v) in self.bits.items():
            eprint("%sBit %i" % ("".join(["  "] * tab_level), k))
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
        r.place(self.inv)

        return start_row

class Word(Placeable):
    def __init__(self, instances):
        self.clkbuf = None
        self.webufs = []
        rbytes = {}

        for instance in instances:
            n = instance.getName()

            clkbuf = r"\bCLKBUF\b"
            webuf = r"\bWEBUF\b"
            byte = r"\bB(\d+)\b"

            if cb_match := re.search(clkbuf, n):
                self.clkbuf = instance
            elif wb_match := re.search(webuf, n):
                self.webufs.append(instance)
            elif byte_match := re.search(byte, n):
                i = int(byte_match[1])
                rbytes[i] = rbytes.get(i) or []
                rbytes[i].append(instance)

        self.bytes = {}
        for k, v in rbytes.items():
            self.bytes[k] = Byte(v)

        byte_count = len(self.bytes.items())
        webuf_count = len(self.webufs)
        if webuf_count != byte_count:
            raise DataError("Write enable buffer count and byte buffer count mismatched: (%i/%i)" % (webuf_count, byte_count))

    def represent(self, tab_level=-1):
        tab_level += 1

        eprint("%sClock Buffer %s" % ("".join(["  "] * tab_level), RepresentInstance(self.clkbuf)))

        eprint("%sWrite Enable Buffers" % "".join(["  "] * tab_level))
        tab_level += 1
        for instance in self.webufs:
            eprint("%s%s" % ("".join(["  "] * tab_level), RepresentInstance(instance)))
        tab_level -= 1

        eprint("%sBytes" % "".join(["  "] * tab_level))
        tab_level += 1
        for (k, v) in self.bytes.items():
            eprint("%sByte %i" % ("".join(["  "] * tab_level), k))
            v.represent(tab_level=tab_level)
        tab_level -= 1

    def place(self, row_list, start_row=0):
        r = row_list[start_row]

        bytes_sorted = list(self.bytes.items())
        bytes_sorted.sort(reverse=True, key=lambda x: x[0])

        for k, v in bytes_sorted:
            v.place(row_list, start_row)
            r.place(self.webufs[k])
        
        r.place(self.clkbuf)

        return start_row

class Slice(Placeable): # A slice is defined as 8 words.
    def __init__(self, instances):
        rwords = {}
        self.decoder_and = []
        self.decoder_abuf = []
        self.decoder_enbuf = None

        for instance in instances:
            n = instance.getName()

            word = r"\bWORD\\\[(\d+)\\\]"
            dand = r"\bAND(\d+)\b"
            abuf = r"\bABUF\\\[(\d+)\\\]"
            enbuf = r"\bENBUF\b"

            if word_match := re.search(word, n):
                i = int(word_match[1])
                rwords[i] = rwords.get(i) or []
                rwords[i].append(instance)
            elif and_match := re.search(dand, n):
                and_number = int(and_match[1])
                self.decoder_and.append((and_number, instance))
            elif abuf_match := re.search(abuf, n):
                abuf_number = int(abuf_match[1])
                self.decoder_abuf.append((abuf_number, instance))
            elif enbuf_match := re.search(enbuf, n):
                self.decoder_enbuf = instance

        self.decoder_and.sort(key=lambda x: x[0])
        self.decoder_and = list(map(lambda x: x[1], self.decoder_and))

        self.decoder_abuf.sort(key=lambda x: x[0])
        self.decoder_abuf = list(map(lambda x: x[1], self.decoder_abuf))

        self.words = {}
        for (k, v) in rwords.items():
            self.words[k] = Word(v)

        word_count = len(self.words.keys())
        if word_count != 8:
            raise DataError("Slice has (%i/8) words." % word_count) 

    def represent(self, tab_level=-1):
        tab_level += 1

        eprint("%sDecoder" % "".join(["  "] * tab_level))
        tab_level += 1
        for instance in self.decoder_and + self.decoder_abuf + [self.decoder_enbuf]:
            eprint("%s%s" % ("".join(["  "] * tab_level), RepresentInstance(instance)))
        tab_level -= 1

        eprint("%sWords" % "".join(["  "] * tab_level))
        tab_level += 1
        for (k, v) in self.words.items():
            eprint("%sWord %i" % ("".join(["  "] * tab_level), k))
            v.represent(tab_level=tab_level)
        tab_level -= 1

    def place(self, row_list, start_row=0):
        current_row = start_row
        words_sorted = list(self.words.items())
        words_sorted.sort(reverse=True, key=lambda x: x[0])

        for _, word in words_sorted:
            word.place(row_list, current_row)
            current_row += 1

        last_column = [self.decoder_abuf[0], None, self.decoder_abuf[1], None, self.decoder_abuf[2], None, self.decoder_enbuf]
        for i in range(8):
            r = row_list[i]
            andi = self.decoder_and[i]
            r.place(andi)
            if i % 2 == 0:
                r.place(last_column[i])        

        return current_row + 8