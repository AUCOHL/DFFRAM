try:
    import opendbpy as odb
except ImportError:
    print(
    """
    You need to install opendb (Ahmed Ghazy's fork):
    https://github.com/ax3ghazy/opendb
    Build normally then go to ./build/src/swig/python and run setup.py

    (On macOS rename the .dylib to .so first)
    """)
    exit(-1)

try:
    import click
except ImportError:
    print("You need to install click: python3 -m pip install click")
    exit(-1)


import os
import re
import math
import pprint
import argparse
import traceback
from functools import reduce

class Cluster:
    def __init__(self, number):
        self.number = number

        self.words = {}
        self.webufs = []
        self.dibufs = []
        self.clkbufs = []

        self.floatbufs = []

        self.decoders = []
        self.decoder_abufs = []

class Placer:
    TAP_CELL_NAME = "sky130_fd_sc_hd__tapvpwrvgnd_1"
    TAP_DISTANCE = 6

    def __init__(self, lef, tech_lef, df):
        # Initialize Database
        self.db = odb.dbDatabase.create()

        # Process LEF Data
        self.tlef = odb.read_lef(self.db, tech_lef)
        self.lef = odb.read_lef(self.db, lef)

        self.tech = self.db.getTech()

        self.sites = self.tlef.getSites()
        self.regular_site = self.sites[0]

        self.site_width = self.regular_site.getWidth()
        self.site_height = self.regular_site.getHeight()

        self.cells = self.lef.getMasters()

        ## Extract the tap cell for later use
        self.tap_cell = list(filter(lambda x: x.getName() == Placer.TAP_CELL_NAME, self.cells))[0]
        self.tap_cell_counter = 0

        # Process DEF data
        self.df = odb.read_def(self.db, df)

        self.chip = self.db.getChip()
        self.block = self.chip.getBlock()

        self.clusters = {}

        self.outputs = []

        self.miscellaneous = []

        self.instances = self.block.getInsts()

        self.rows = self.block.getRows()
        self.rows.reverse() # Reverse the order of the rows so that placement starts at the top instead of the bottom

        # Parse DEF instances
        def gi(str):
            rx = r"\w+\\\[(\d+)\\\]"
            result = re.match(rx, str)
            if result is None:
                return None
            return int(result[1])

        def ag(dictionary, key):
            if dictionary.get(key) is None:
                dictionary[key] = []
            return dictionary[key]

        def dg(dictionary, key):
            if dictionary.get(key) is None:
                dictionary[key] = {}
            return dictionary[key]

        def cg(dictionary, key, number):
            if dictionary.get(key) is None:
                dictionary[key] = Cluster(number)
            return dictionary[key]

        def has_prefix(namec, prefix):
            for el in namec:
                if el.startswith(prefix):
                    return el
            return None

        print("Found %i instances." % len(self.instances))

        for instance in self.instances:
            name = instance.getName()
            namec = name.split('.')
            top = namec[0]

            if top.startswith("COLUMN"):
                number = gi(top)
                cluster = cg(self.clusters, top, number)
                
                if word_name := has_prefix(namec, "WORD"):
                    current_word = ag(cluster.words, word_name)
                    current_word.append(name)
                elif webuf_name := has_prefix(namec, "WEBUF"):
                    cluster.webufs.append(name)
                elif dibuf_name := has_prefix(namec, "DIBUF"):
                    cluster.dibufs.append(name)
                elif clkbuf_name := has_prefix(namec, "CLKBUF"):
                    cluster.clkbufs.append(name)
                elif floatbuf_name := has_prefix(namec, "FLOATBUF"):
                    cluster.floatbufs.append(name)
                elif "DEC" in namec:
                    if abuf_name := has_prefix(namec, "ABUF"):
                        cluster.decoder_abufs.append(name)
                    else:
                        cluster.decoders.append(name)
                else:
                    self.miscellaneous.append(name)
            elif output_name := has_prefix(namec, "Do"):
                ag(self.outputs, top).append(name)
            else:
                self.miscellaneous.append(name)

    def create_tap(self, current_row, current_point):
        instance = odb.dbInst_create(self.block, self.tap_cell, "tap_cell_%i" % self.tap_cell_counter)
        self.tap_cell_counter += 1

        row_orientation = current_row.getOrient()

        instance.setOrient(row_orientation)
        instance.setLocation(current_point[0], current_point[1])
        instance.setPlacementStatus("PLACED")

        current_point[0] += self.site_width * math.ceil(instance.getMaster().getWidth() / self.site_width)

        return current_point

    def place_generic(self, cells, current_row_index, current_point):
        row = self.rows[current_row_index]
        row_orientation = row.getOrient()

        for i, cell in enumerate(cells):
            instance = self.block.findInst(cell)
            if (current_row_index % Placer.TAP_DISTANCE) == 0:
                if (i % Placer.TAP_DISTANCE == 0):
                    current_point = self.create_tap(row, current_point)
            
            if ((current_row_index + Placer.TAP_DISTANCE / 2) % Placer.TAP_DISTANCE == 0):
                if ((i + Placer.TAP_DISTANCE / 2) % Placer.TAP_DISTANCE == 0):
                    current_point = self.create_tap(row, current_point)
                
            instance.setOrient(row_orientation)
            instance.setLocation(current_point[0], current_point[1])
            instance.setPlacementStatus("PLACED")

            current_point[0] += self.site_width * math.ceil(instance.getMaster().getWidth() / self.site_width)
        
        return current_row_index

    def place_buffers(self, buffers, current_row_index):
        row = self.rows[current_row_index]
        row_origin = row.getOrigin()
        current_row_index = self.place_generic(buffers, current_row_index, row_origin)
        return current_row_index

    # Places cells of a 4-byte word
    def place_word(self, word, current_row_index, current_point):
        bytes = [[], [], [], []]

        def gb(str):
            rx = r".+?\.B(\d+)\."
            result = re.match(rx, str)
            if result is None:
                return None
            return int(result[1])
        
        for cell in word:
            bytes[gb(cell)].append(cell)

        bytes.reverse()
        current_row_index = self.place_generic(reduce(lambda x, y: x + y, bytes), current_row_index, current_point)

        return (current_point, current_row_index)


    def place_cluster(self, cluster, current_row_index):
        buffers = []
        buffers += cluster.clkbufs
        buffers += cluster.dibufs
        buffers += cluster.webufs
        buffers += cluster.floatbufs

        current_row_index = self.place_buffers(buffers, current_row_index)
        row = self.rows[current_row_index]
        row_origin = row.getOrigin()
        row_orientation = row.getOrient()

        current_point = row_origin
        word_count = len(cluster.words)

        print("Placing cluster %i: %i words…" % (cluster.number, word_count))

        decoder_cells = cluster.decoders + cluster.decoder_abufs

        decoder_cells_per_row = math.ceil(float(len(decoder_cells)) / word_count)

        row_tracker = 0

        for (_, word) in cluster.words.items():
            current_point, current_row_index = self.place_word(word, current_row_index, current_point)

            start = decoder_cells_per_row * row_tracker
            finish = (decoder_cells_per_row * row_tracker) + decoder_cells_per_row - 1

            current_row_index = self.place_generic(decoder_cells[start:finish], current_row_index, current_point)
            current_row_index += 1

        return current_row_index

    def place_clusters(self, current_row_index):
        for cluster in self.clusters.values():
            current_row_index = self.place_cluster(cluster, current_row_index)
            current_row_index += 2 # why?
        return current_row_index

    def place(self):
        current_row_index = self.place_clusters(0)
        
        print("Placing miscellaneous instances (%i)…" % len(self.miscellaneous))
        current_row_index = self.place_buffers(self.miscellaneous, current_row_index)
        print("Placed %i rows." % current_row_index)
        print("Placed %i tap cells." % self.tap_cell_counter)

    def write_def(self, output):
        return odb.write_def(self.chip.getBlock(), output) == 1

@click.command()
@click.option('-o', '--output', required=True)
@click.option('-l', '--lef', required=True)
@click.option('-t', '--tech-lef', "tlef", required=True)
@click.argument('def_file', required=True, nargs=1)
def cli(output, lef, tlef, def_file):
    placer = Placer(lef, tlef, def_file)
    placer.place()
    if not placer.write_def(output):
        raise Exception("Failed to write output DEF file.")
    else:
        print("Wrote %s." % output)
        print("Done.")

def main():
    try:
        cli()
    except Exception:
        print("An unexpected exception has occurred.", traceback.format_exc())
        exit(-1)

if __name__ == '__main__':
    main()
