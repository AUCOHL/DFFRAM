#!/usr/bin/env python3
# -*- coding: utf8 -*-
# Copyright ©2021 The American University in Cairo
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

try:
    import click
except ImportError:
    print("You need to install click: python3 -m pip install click")
    exit(os.EX_CONFIG)

import re


def remove_mcon_from_port(lef: str):
    final = []
    # states:
    #  -1 -> start: MACRO {macro_name} ; -> 0
    #   0 -> in design: PORT -> 1, END {macro_name} -> -1
    #   1 -> in port: END -> 0, LAYER mcon ; -> 2
    #   2 -> in layer mcon LAYER -> 1, END -> 0, else do not print
    state = -1

    macro_start_rx = re.compile(r"^\s*MACRO\s+sky130_fd_sc_hd__dlclkp_1\s*$")
    macro_end_rx = re.compile(r"^\s*END\s+sky130_fd_sc_hd__dlclkp_1\s*$")
    port_rx = re.compile(r"^\s*PORT\s*$")
    end_rx = re.compile(r"^\s*END\s*$")
    mcon_rx = re.compile(r"^\s*LAYER\s+mcon\s*;\s*$")
    layer_rx = re.compile(r"^\s*LAYER\s*\w+\s*;\s*$")
    for line in lef.split("\n"):
        if state == -1:
            if macro_start_rx.match(line):
                state = 0
            final.append(line)
        elif state == 0:
            if port_rx.match(line):
                state = 1
            if macro_end_rx.match(line):
                state = -1
            final.append(line)
        elif state == 1:
            if end_rx.match(line):
                state = 0
                final.append(line)
            elif mcon_rx.match(line):
                state = 2
            else:
                final.append(line)
        elif state == 2:
            if layer_rx.match(line):
                state = 1
                final.append(line)
            if end_rx.match(line):
                state = 0
                final.append(line)

    return "\n".join(final)


def process_lefs(lef, output_cells):
    with open(output_cells, "w") as f:
        input_str = open(lef).read()
        f.write(remove_mcon_from_port(input_str))


@click.command(
    help="A hack for sky130_fd_sc_hd-based designs to route properly with current versions of OpenROAD."
)
@click.option("-l", "--lef", required=True)
@click.option("-C", "--output-cells", required=True)
def main(lef, output_cells):
    process_lefs(lef, output_cells)


if __name__ == "__main__":
    main()
