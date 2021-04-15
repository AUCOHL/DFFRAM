from prflow.cli import write_script_to_file
from prflow.scripts import floorplanTclScript
from prflow.config import *
from pathlib import Path
import pathlib
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
from .data import Block, Slice, HigherLevelPlaceable
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

    SUPPORTED_WORD_COUNTS = [8, 32, 128]

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

        self.block = self.db.getChip().getBlock()

        self.instances = self.block.getInsts()
        eprint("Found %i instances…" % len(self.instances))

        def create_tap(name):
            return odb.dbInst_create(self.block, self.tap_cell, name)

        def create_fill(name, sites=1):
            fill_cell = self.fill_cells_by_sites[sites]
            return odb.dbInst_create(self.block, fill_cell, name)

        self.micron_in_units = self.block.getDefUnits()
        tap_distance = self.micron_in_units * Placer.TAP_DISTANCE_MICRONS

        self.rows = Row.from_odb(self.block.getRows(), self.sites[0], create_tap, tap_distance, create_fill, fill_cell_sizes)

        # TODO: E X P A N D
        if word_count == 8:
            self.hierarchy = Slice(self.instances)
        elif word_count == 32:
            self.hierarchy = Block(self.instances)
        elif word_count >= 128:
            self.hierarchy = HigherLevelPlaceable(self.instances)

    def represent(self, file):
        self.hierarchy.represent(file=file)

    def place(self):
        eprint("Starting placement…")
        last_row = self.hierarchy.place(self.rows)

        # We can't rely on the fact that a placeable will probably fill
        # before returning and pick the width of the nth row or whatever.
        width_units = 0
        for row in self.rows:
            width_units = max(row.x, width_units)

        self.core_width = width_units / self.micron_in_units

        height_units = self.rows[last_row-1].ymax - self.rows[0].y

        self.core_height = height_units / self.micron_in_units


        eprint("Placement concluded with core size of %fµm x
                %fµm." % (self.core_width, self.core_height))

        self.core_height += 3
        single_row_height = 3
        global SIZE
        print("the size read is ", SIZE)
        DESIGN = DESIGN_of(SIZE)
        BUILD_FOLDER = BUILD_FOLDER_of(DESIGN)

        floorplanTclScriptFilled = floorplanTclScript.format(
                BUILD_FOLDER,
                DESIGN,
                DESIGN,
                width+MARGIN,
                (single_row_height+self.core_height)+MARGIN,
                MARGIN, MARGIN, width,
                single_row_height+self.core_height,
                BUILD_FOLDER, DESIGN)

        build_folder = pathlib.Path(BUILD_FOLDER)
        write_script_to_file(floorplanTclScriptFilled,
                "fp_init.tcl", build_folder)
        eprint("Done.")

    def unplace_fills(self):
        eprint("Unplacing fills…")
        for instance in self.block.getInsts():
            kind = instance.getMaster().getName()
            match = re.match(Placer.FILL_CELL_RX, kind)
            print(Placer.FILL_CELL_RX, kind, match)
            if match is not None:
                instance.setPlacementStatus("UNPLACED")

    def write_def(self, output):
        return odb.write_def(self.block, output) == 1

    def write_width(self):


        with open(CORE_WIDTH_POSTPLACEMENT_FILE,
                "w+") as core_width_file:
            written_bytes = core_width_file.write(self.core_width)
        return written_bytes

    def write_height(self):
        with open(CORE_HEIGHT_POSTPLACEMENT_FILE,
                "w+") as core_height_file:
            written_bytes = core_height_file.write(self.core_width)
        return written_bytes

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
@click.option('--unplace-fills/--no-unplace-fills', default=False, help="Removes placed fill cells to show fill-free placement. Debug option.")
@click.argument('def_file', required=True, nargs=1)
def cli(output, lef, tlef, size, represent, unplace_fills, def_file):
    global SIZE
    SIZE = size
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

    if unplace_fills:
        placer.unplace_fills()

    if not placer.write_def(output):
        eprint("Failed to write output DEF file.")
        exit(73)
    else:
        eprint("Wrote to %s." % output)
        eprint("Done.")
    if not placer.write_width():
        eprint("Failed to write core width file.")
        exit(73)
    else:
        eprint("Wrote width")
        eprint("Done.")

    if not placer.write_height():
        eprint("Failed to write core height file.")
        exit(73)
    else:
        eprint("Wrote height)
        eprint("Done.")

def main():
    try:
        cli()
    except Exception:
        print("An unexpected exception has occurred.", traceback.format_exc())
        exit(69)
