#!/usr/bin/env python3
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
import odb

import os
import re
import sys
import traceback

try:
    import click
    import yaml
except ImportError:
    print("You need to install click and pyyaml: python3 -m pip install click pyyaml")
    exit(os.EX_CONFIG)


@click.command()
@click.option(
    "--from-fills-file",
    "fill_cells_file",
    default=None,
    help="Load regular expressions of cell masters to remove from a fill_cells.yml file.",
)
@click.option(
    "--include-tap/--exclude-tap",
    default=True,
    help="When loading from a fill_cells.yml file, include tap cells in removal or not.",
)
@click.option(
    "--from-string",
    "rxs_string",
    default=None,
    help="Load regular expressions of cell masters to remove. semicolon;delimited",
)
@click.option(
    "-o",
    "--output",
    "output_file",
    default=None,
    help="Output file",
    show_default=True,
)
@click.argument("input_file", required=True)
def unplace(fill_cells_file, rxs_string, include_tap, output_file, input_file):
    if output_file is None:
        output_file = input_file

    rx_list = []
    if fill_cells_file is not None and rxs_string is None:
        try:
            fill_yml_str = open(fill_cells_file).read()
        except FileNotFoundError:
            print(f"{fill_cells_file} not found.", file=sys.stderr)
            exit(os.EX_NOINPUT)

        data: dict = yaml.load(fill_yml_str, Loader=yaml.SafeLoader)
        for key, value in data.items():
            if not include_tap and key == "tap":
                continue
            rx_list.append(value)
    elif rxs_string is not None and fill_cells_file is None:
        rx_list += rxs_string.split(";")
    else:
        print(
            "Exactly one of --from-file and --from-string are required.",
            file=sys.stderr,
        )

    rx_list = [re.compile(rx) for rx in rx_list]

    db = odb.dbDatabase.create()
    odb.read_db(db, input_file)

    block = db.getChip().getBlock()

    removed = 0
    removed_nets = 0
    for instance in block.getInsts():
        master_name = instance.getMaster().getName()
        for rx in rx_list:
            match = rx.match(master_name)
            if match is None:
                continue
            for iterm in instance.getITerms():
                net = iterm.getNet()
                iterm.clearConnected()
                if net is not None and len(net.getITerms()) == 0:
                    odb.dbNet.destroy(net)
                    removed_nets += 1
            odb.dbInst.destroy(instance)
            removed += 1
            break

    odb.write_db(db, output_file)

    print(f"Removed {removed} instances and {removed_nets} nets.")


def main():
    try:
        unplace()
    except Exception:
        print(
            "An unhandled exception has occurred.",
            traceback.format_exc(),
            file=sys.stderr,
        )
        exit(os.EX_UNAVAILABLE)


if __name__ == "__main__":
    main()
