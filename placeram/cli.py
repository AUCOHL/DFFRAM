# -*- coding: utf8 -*-
# Copyright ©2020-2022 The American University in Cairo
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

import os
import re
import traceback

try:
    import odb
    import utl
except ImportError:
    print(
        """
        placeram needs to be inside OpenROAD:

        openroad -python -m placeram [args]
        """
    )
    exit(os.EX_CONFIG)

try:
    import click
except ImportError:
    print("You need to install click: python3 -m pip install click")
    exit(os.EX_CONFIG)

try:
    import yaml
except ImportError:
    print("You need to install pyyaml: python3 -m pip install pyyaml")
    exit(os.EX_CONFIG)

from . import data
from .row import Row

from .util import eprint
from .reg_data import DFFRF


class Placer:
    def __init__(
        self,
        odb_in,
        word_count,
        word_width,
        register_file,
        fill_cell_data,
        tap_distance,
    ):
        # Initialize Database
        self.db = odb.dbDatabase.create()

        odb.read_db(self.db, odb_in)

        # Technology Setup
        self.libs = self.db.getLibs()
        self.sites = []
        self.cells = []
        for lib in self.libs:
            self.sites += lib.getSites()
            self.cells += lib.getMasters()

        ## Extract the fill cells for later use
        ### We use decap cells to substitute fills wherever possible.
        raw_fill_cells = list(
            filter(lambda x: re.match(fill_cell_data["fill"], x.getName()), self.cells)
        )
        raw_decap_cells = list(
            filter(lambda x: re.match(fill_cell_data["decap"], x.getName()), self.cells)
        )
        raw_tap_cells = list(
            filter(lambda x: re.match(fill_cell_data["tap"], x.getName()), self.cells)
        )
        self.fill_cells_by_sites = {}
        tap_width = None
        for cell in raw_fill_cells:
            match_info = re.match(fill_cell_data["fill"], cell.getName())
            site_count = int(match_info[1])
            self.fill_cells_by_sites[site_count] = cell
        for cell in raw_decap_cells:
            match_info = re.match(fill_cell_data["decap"], cell.getName())
            site_count = int(match_info[1])
            self.fill_cells_by_sites[site_count] = cell
        for cell in raw_tap_cells:
            match_info = re.match(fill_cell_data["tap"], cell.getName())
            site_count = cell.getWidth() / self.sites[0].getWidth()
            self.fill_cells_by_sites[site_count] = cell
            tap_width = site_count

        fill_cell_sizes = list(self.fill_cells_by_sites.keys())

        if tap_width is None:
            eprint("No tap cells found!")
            print(fill_cell_sizes)
            exit(-1)

        # Layout Setup
        self.block = self.db.getChip().getBlock()
        self.instances = self.block.getInsts()
        eprint("Found %i instances…" % len(self.instances))

        def create_fill(name, sites=1):
            fill_cell = self.fill_cells_by_sites[sites]
            return odb.dbInst_create(self.block, fill_cell, name)

        self.micron_in_units = self.block.getDefUnits()
        tap_distance = self.micron_in_units * tap_distance

        self.rows = Row.from_odb(
            self.block.getRows(),
            self.sites[0],
            tap_distance,
            create_fill,
            fill_cell_sizes,
            fill_cell_data["tap"],
            tap_width,
        )

        if register_file:
            self.hierarchy = DFFRF(self.instances)
        else:
            self.hierarchy = data.create_hierarchy(self.instances, word_count)

        self.fill_cell_data = fill_cell_data

    def represent(self, file):
        self.hierarchy.represent(file=file)

    def place(self):
        eprint("Starting placement…")
        print(f"Placing across {len(self.rows)} rows...")
        last_row = self.hierarchy.place(self.rows)
        print(f"Placement concluded with {last_row} rows...")
        Row.fill_rows(self.rows, 0, last_row)

        # We can't rely on the fact that a placeable will probably fill
        # before returning and pick the width of the nth row or whatever.
        width_units = 0
        for row in self.rows:
            width_units = max(row.width, width_units)

        self.core_width = width_units / self.micron_in_units

        height_units = self.rows[last_row - 1].ymax - self.rows[0].y

        self.core_height = height_units / self.micron_in_units

        logical_area: float = 0
        for cell in self.block.getInsts():
            master = cell.getMaster()
            master_name = master.getName()
            type = "nonfiller"
            for incoming_type, rx in self.fill_cell_data.items():
                if re.match(rx, master_name) is not None:
                    type = incoming_type
                    break
            if type not in ["nonfiller"]:
                continue
            width = master.getWidth() / self.micron_in_units
            height = master.getHeight() / self.micron_in_units
            logical_area += width * height

        eprint(
            "Placement concluded with core area of %fµm x %fµm."
            % (self.core_width, self.core_height)
        )

        utl.metric_float("dffram__suggested__core_width", self.core_width)
        utl.metric_float("dffram__suggested__core_height", self.core_height)

        die_width = self.block.getDieArea().dx() / self.micron_in_units
        die_height = self.block.getDieArea().dy() / self.micron_in_units
        die_area = die_width * die_height

        self.density = logical_area / die_area
        utl.metric_float("dffram__logic__density", self.density)
        eprint("Density: %.2f%%" % (self.density * 100))
        eprint("Done.")

    def write_db(self, output):
        return odb.write_db(self.db, output) == 1

    def write_def(self, output):
        return odb.write_def(self.block, output) == 1


def check_readable(file):
    with open(file, "r"):
        pass


@click.command()
@click.option("-o", "--output-odb", required=True)
@click.option("--output-def", type=str, required=False, default=None)
@click.option("-s", "--size", required=True, help="RAM Size (ex. 8x32, 16x32…)")
@click.option(
    "-r",
    "--represent",
    required=False,
    help="File to print out text representation of hierarchy to. (Pass /dev/stderr or /dev/stdout for stderr or stdout.)",
)
@click.option(
    "-b",
    "--building-blocks",
    default="sky130A:sky130_fd_sc_hd:ram",
    help="Format <pdk>:<scl>:<name> : Name of the building blocks to use.",
)
@click.option(
    "-l",
    "--input-lef",
    default=[],
    help="Input LEF files (ignored)",
    multiple=True,
    type=str,
)
@click.argument("odb_in", required=True, nargs=1)
def cli(
    output_odb,
    output_def,
    input_lef,
    size,
    represent,
    building_blocks,
    odb_in,
):
    pdk, scl, blocks = building_blocks.split(":")
    fill_cells_file = os.path.join(".", "platforms", pdk, "fill_cells.yml")
    if not os.path.isfile(fill_cells_file):
        eprint("Platform %s not found." % pdk)
        exit(os.EX_NOINPUT)

    blocks_config_file = os.path.join(".", "models", blocks, "config.yml")
    blocks_config = yaml.safe_load(open(blocks_config_file))

    register_file = blocks_config.get("register_file") or False

    m = re.match(r"(\d+)x(\d+)", size)
    if m is None:
        eprint("Invalid RAM size '%s'." % size)
        exit(os.EX_USAGE)
    words = int(m[1])
    word_length = int(m[2])
    if words % 8 != 0 or words == 0:
        eprint(
            "WARNING: Word count must be a non-zero multiple of 8. Results may be unexpected."
        )
    if word_length % 8 != 0 or words == 0:
        eprint(
            "WARNING: Word length must be a non-zero multiple of 8. Results may be unexpected."
        )

    platform_tech_file = os.path.join(".", "platforms", pdk, scl, "tech.yml")
    platform_tech_config = yaml.safe_load(open(platform_tech_file))

    tap_distance = platform_tech_config["tap_distance"]

    for input in [odb_in]:
        check_readable(input)

    fill_cell_data = yaml.load(open(fill_cells_file).read(), Loader=yaml.SafeLoader)

    placer = Placer(
        odb_in,
        words,
        word_length,
        register_file,
        fill_cell_data,
        tap_distance,
    )

    if represent is not None:
        with open(represent, "w") as f:
            placer.represent(f)

    placer.place()

    if not placer.write_db(output_odb):
        eprint("Failed to write output ODB file.")
        exit(os.EX_IOERR)

    eprint("Wrote to %s." % output_odb)

    if output_def is not None:
        if not placer.write_def(output_def):
            eprint("Failed to write output DEF file.")
            exit(os.EX_IOERR)

    eprint("Done.")


def main():
    try:
        cli()
    except Exception:
        eprint("An unhandled exception has occurred.", traceback.format_exc())
        exit(os.EX_UNAVAILABLE)
