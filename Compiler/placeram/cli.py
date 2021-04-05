try:
    import opendbpy as odb
except ImportError:
    print(
    """
    You need to install opendb (Ahmed Ghazy's fork):
    https://github.com/ax3ghazy/opendb
    Build normally then go to ./build/src/swig/python and run:
    
    python3 setup.py install

    (On macOS rename the .dylib to .so first)
    """)
    exit(78)

try:
    import click
except ImportError:
    print("You need to install click: python3 -m pip install click")
    exit(78)

from .util import eprint
from .data import Block, Slice
from .row import Row

import os
import re
import sys
import math
import pprint
import argparse
import traceback
from functools import reduce

class Placer:
    TAP_CELL_NAME = "sky130_fd_sc_hd__tapvpwrvgnd_1"
    TAP_DISTANCE_MICRONS = 15

    FILL_CELL_RX = r"sky130_fd_sc_hd__fill_(\d+)"

    SUPPORTED_WORD_COUNTS = [8, 32]

    def __init__(self, lef, tech_lef, df, word_count, word_width):
        if word_width != 32:
            eprint("Only 32-bit words are supported so far.")
            exit(64)
        if word_count not in Placer.SUPPORTED_WORD_COUNTS:
            eprint("Only the following word counts are supported so far: %s" % Placer.SUPPORTED_WORD_COUNTS)
            exit(64)

        # Initialize Database
        self.db = odb.dbDatabase.create()

        # Process LEF Data
        self.tlef = odb.read_lef(self.db, tech_lef)
        self.lef = odb.read_lef(self.db, lef)

        self.tech = self.db.getTech()

        self.sites = self.tlef.getSites()

        self.cells = self.lef.getMasters()

        ## Extract the tap cell for later use
        self.tap_cell = list(filter(lambda x: x.getName() == Placer.TAP_CELL_NAME, self.cells))[0]

        ## Extract the fill cell for later use
        raw_fill_cells = list(filter(lambda x: re.match(Placer.FILL_CELL_RX, x.getName()), self.cells))
        self.fill_cells_by_sites = {}
        for cell in raw_fill_cells:
            match_info = re.match(Placer.FILL_CELL_RX, cell.getName())
            site_count = int(match_info[1])
            self.fill_cells_by_sites[site_count] = cell
        fill_cell_sizes = list(self.fill_cells_by_sites.keys())

        # Process DEF data
        self.df = odb.read_def(self.db, df)

        self.chip = self.db.getChip()
        self.block = self.chip.getBlock()

        self.outputs = []

        self.miscellaneous = []

        self.instances = self.block.getInsts()
        eprint("Found %i instances…" % len(self.instances)) 

        def create_tap(name):
            return odb.dbInst_create(self.block, self.tap_cell, name)

        def create_fill(name, sites=1):
            fill_cell = self.fill_cells_by_sites[sites]
            return odb.dbInst_create(self.block, fill_cell, name)

        tap_distance = self.block.getDefUnits() * Placer.TAP_DISTANCE_MICRONS

        self.rows = Row.from_odb(self.block.getRows(), self.sites[0], create_tap, tap_distance, create_fill, fill_cell_sizes)

        # TODO: E X P A N D
        if word_count == 8:
            self.hierarchy = Slice(self.instances)
        elif word_count == 32:
            self.hierarchy = Block(self.instances)

    def represent(self, file):
        self.hierarchy.represent(file=file)

    def place(self):
        eprint("Starting placement…")
        self.hierarchy.place(self.rows)

    def write_def(self, output):
        return odb.write_def(self.chip.getBlock(), output) == 1

# "Ask forgiveness not permission" yeah go and argue that in front of a judge
def check_readable(file):
    with open(file, 'r') as f:
        pass

@click.command()
@click.option('-o', '--output', required=True)
@click.option('-l', '--lef', required=True)
@click.option('-t', '--tech-lef', "tlef", required=True)
@click.option('-s', '--size', required=True, help="RAM Size (ex. 8x32, 16x32…)")
@click.option('-r', '--represent', required=False, help="File to print out text representation of hierarchy to. (Pass /dev/stderr or /dev/stdout for stderr or stdout.)")
@click.argument('def_file', required=True, nargs=1)
def cli(output, lef, tlef, size, represent, def_file):
    m = re.match(r"(\d+)x(\d+)", size)
    if m is None:
        eprint("Invalid RAM size '%s'." % size)
        exit(64)
    words = int(m[1])
    word_length = int(m[2])
    if words % 8 != 0 or words == 0:
        eprint("Word count must be a non-zero multiple of 8.")
        exit(64)
    if word_length % 8 != 0 or words == 0:
        eprint("Word length must be a non-zero multiple of 8.")
        exit(64)

    for input in [lef, tlef, def_file]:
        check_readable(input)

    placer = Placer(lef, tlef, def_file, words, word_length)

    if represent is not None:
        with open(represent, 'w') as f:
            placer.represent(f)

    placer.place()
    if not placer.write_def(output):
        eprint("Failed to write output DEF file.")
        exit(73)
    else:
        eprint("Wrote to %s." % output)
        eprint("Done.")

def main():
    try:
        cli()
    except Exception:
        print("An unexpected exception has occurred.", traceback.format_exc())
        exit(69)