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
    exit(78)

try:
    import click
except ImportError:
    print("You need to install click: python3 -m pip install click")
    exit(78)

from .util import eprint
from .data import Slice, Row

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

    def __init__(self, lef, tech_lef, df, word_count, word_width):
        if word_width != 32:
            eprint("Only 32-bit words are supported for now.")
            exit(69)

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
        self.tap_cell_counter = 0

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

        tap_distance = self.block.getDefUnits() * Placer.TAP_DISTANCE_MICRONS

        self.rows = Row.from_odb(self.block.getRows(), self.sites[0], create_tap, tap_distance)

        self.hierarchy = Slice(self.instances)

    def place(self):
        eprint("Starting placement…")
        self.hierarchy.place(self.rows)

    def write_def(self, output):
        return odb.write_def(self.chip.getBlock(), output) == 1

@click.command()
@click.option('-o', '--output', required=True)
@click.option('-l', '--lef', required=True)
@click.option('-t', '--tech-lef', "tlef", required=True)
@click.option('-s', '--size', required=True, help="RAM Size (ex. 8x32, 16x32…)")
@click.argument('def_file', required=True, nargs=1)
def cli(output, lef, tlef, size, def_file):
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

    placer = Placer(lef, tlef, def_file, words, word_length)
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