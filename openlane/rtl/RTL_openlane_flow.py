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

from DFFRAM_template import parameterized_module, parameterized_config, pin_order_cfg, pdn_tcl_cfg


def rp(path):
    return os.path.realpath(path)

def ensure_dir(path):
    return pathlib.Path(path).mkdir(parents=True, exist_ok=True)

def write_file(filename, data):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w+') as f:
        print("writing file %s" % filename)
        f.write(data)

def run_docker(image, args, pdk_path, interactive=False):
    subprocess.run([
        "docker", "run",
        "-tiv" if interactive else "-v",
        "%s:/mnt/dffram" % rp(".."),
        "-v", "%s:/openLANE_flow/designs" % rp("designs"),
        "-v", "%s:/pdks" % rp(pdk_path),
        "-e", "PDK_ROOT=%s" % "/pdks",
        "-w", "/openLANE_flow",
    ] + [image] + args, check=True)

def openlane(*args_tuple, pdk_path, interactive=False):
    args = list(args_tuple)
    run_docker("efabless/openlane:current", args, pdk_path)

def gen_v_file(size, design, filename):
    size = int(size)
    module = parameterized_module.format(size=int(size),
                                        words_num=int(size/4),
                                        addr_width=int(math.log2(size/4)))
    write_file(filename, module)



def gen_cfg_file(size, design, cfg_filename):
    cfg = parameterized_config.format(size=int(size),
            design=design)
    write_file(cfg_filename, cfg)

@click.command()
@click.option("-s", "--size",
        default=512,
        help="size in bytes")
@click.option("-t", "--tag",
        default="{:%Y_%m_%d_%H_%M_%S}".format(datetime.now()),
        help="size in bytes")
@click.option("-p", "--pdk_path",
        default="/pdks",
        help="path to the pdk directory")
def RTL_openlane_flow(size, tag, pdk_path):
    designs_folder = 'designs'
    design = "DFFRAM_RTL_{size}".format(size=size)
    def filepath_src(ext=""):
        return "%s/%s/src/%s%s" %(designs_folder, design, design, ext)
    def filepath_src_docker(ext=""):
        return "/mnt/dffram/RTL/%s/%s/src/%s%s" %(designs_folder, design, design, ext)
    def filepath(ext):
        return "%s/%s/%s%s" %(designs_folder, design, design, ext)
    def filepath_unnamed(name, ext):
        return "%s/%s/%s%s" %(designs_folder, design, name, ext)
    def filepath_docker(ext=""):
        return "/mnt/dffram/RTL/%s/%s/%s%s" %(designs_folder, design, design, ext)

    verilog_filename = filepath_src(".v")
    cfg_filename = filepath(".tcl")
    pdn_cfg_filename = filepath_unnamed("pdn", ".tcl")
    pin_order_cfg_filename = filepath_unnamed("pin_order", ".cfg")
    gen_v_file(size, design, verilog_filename)
    gen_cfg_file(size, design, cfg_filename)
    write_file(pin_order_cfg_filename, pin_order_cfg)
    write_file(pdn_cfg_filename, pdn_tcl_cfg)
    openlane("tclsh", "flow.tcl",
            "-design", design,
            "-tag", tag,
            "-src", filepath_src_docker(".v"),
            "-config_file", filepath_docker(".tcl"), pdk_path=pdk_path)

def main():
    try:
        RTL_openlane_flow()
    except Exception:
        print("An unhandled exception has occurred.", traceback.format_exc())
        exit(69)

if __name__ == '__main__':
    main()
