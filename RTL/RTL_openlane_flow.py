#!/usr/bin/env python3
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
try:
    import click
except ImportError:
    print("You need to install click: python3 -m pip install click")
    exit(78)

import os
import re
import time
import pathlib
import textwrap
import traceback
import subprocess
import math
from datetime import datetime, date

from DFFRAM_template import parameterized_module


def rp(path):
    return os.path.realpath(path)

def ensure_dir(path):
    return pathlib.Path(path).mkdir(parents=True, exist_ok=True)

def run_docker(image, args, interactive=False):
    subprocess.run([
        "docker", "run",
        "-tiv" if interactive else "-v",
        "%s:/mnt/dffram" % rp(".."),
        "-w", "/mnt/dffram/RTL",
    ] + [image] + args, check=True)

def openlane(*args_tuple, interactive=False):
    args = list(args_tuple)
    run_docker("efabless/openlane", args)

def gen_v_file(size, design, filename):
    size = int(size)
    module = parameterized_module.format(size=int(size),
                                        words_num=int(size/4),
                                        addr_width=int(math.log2(size/4)))
    with open(filename, 'w+') as f:
        f.write(module)

@click.command()
@click.option("-s", "--size", default=512, help="size in bytes")
@click.option("-t", "--tag", default="", help="size in bytes")
def RTL_openlane_flow(size):
    designs_folder = './designs'
    design = "DFFRAM_RTL_{size}".format(size=size)
    def i(ext=""):
        return "%s/%s%s" %(designs_folder, design, ext)

    filename = i(".v")
    gen_v_file(size, design, filename)
    openlane("tclsh", "flow.tcl",
            "-design", design,
            "-tag", "{:%Y_%m_%d_%H_%M_%S}".format(datetime.now()),
            "-src", filename)

def main():
    try:
        RTL_openlane_flow()
    except Exception:
        print("An unhandled exception has occurred.", traceback.format_exc())
        exit(69)

if __name__ == '__main__':
    main()
