#!/usr/bin/env python3
# -*- coding: utf8 -*-
# Copyright ©2020-2021 The American University in Cairo and the Cloud V Project.
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
import sys
import traceback
try:
    import click
    import yaml
except ImportError:
    print("You need to install click and pyyaml: python3 -m pip install click pyyaml")
    exit(os.EX_CONFIG)

@click.command()
@click.option("-p", "--platform", required=True, help="PDK/Platform to use, e.g. sky130A")
@click.option("-o", "--output", "output_file", default="/dev/stdout", help="Output file", show_default=True)
@click.argument("input_file", required=True)
def unplace(platform, output_file, input_file):
    dn = os.path.dirname
    dffram_path = dn(dn(dn(os.path.abspath(__file__))))
    fill_yml_path = os.path.join(dffram_path, "platforms", platform, "fill_cells.yml")
    try:
        fill_yml_str = open(fill_yml_path).read()
    except FileNotFoundError:
        print(f"{fill_yml_path} not found.", file=sys.stderr)
        exit(os.EX_NOINPUT)

    data: dict = yaml.load(fill_yml_str, Loader=yaml.SafeLoader)
    rx_list = list(data.values())

    try:
        input_str = open(input_file).read()
    except FileNotFoundError:
        print(f"{input_file} not found.", file=sys.stderr)
        exit(os.EX_NOINPUT)

    output_str = input_str
    
    replaced = 0
    for rx in rx_list:
        frx = fr"({rx})\s*\+\s*PLACED\s*\(\s*\d+\s*\d+\s*\)\s*\w+"
        output_str, replacements = re.subn(frx, r"\1", output_str)
        replaced += replacements


    with open(output_file, "w") as f:
        f.write(output_str)

    print(f"Done. Unplaced {replaced} instances.", file=sys.stderr)

def main():
    try:
        unplace()
    except Exception:
        print("An unhandled exception has occurred.", traceback.format_exc(), file=sys.stderr)
        exit(os.EX_UNAVAILABLE)

if __name__ == '__main__':
    main()
