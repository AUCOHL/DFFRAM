#!/usr/bin/env python3
# -*- coding: utf8 -*-
# Copyright ©2020-2022 The American University in Cairo and the Cloud V Project.
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
import pathlib
import traceback
import subprocess
from datetime import datetime

import click
from mako.lookup import TemplateLookup


def rp(path):
    return os.path.realpath(path)


def ensure_dir(path):
    return pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def openlane(*args_tuple, pdk_path=None, interactive=False):
    subprocess.run(
        [
            "docker",
            "run",
            "-tiv" if interactive else "-v",
            "%s:/mnt/dffram" % rp(".."),
            "-v",
            "%s:/openlane/designs" % rp("designs"),
            "-v",
            "%s:/pdks" % rp(pdk_path or os.getenv("PDK_ROOT")),
            "-e",
            "PDK_ROOT=%s" % "/pdks",
            "-w",
            "/openlane",
        ]
        + ["efabless/openlane:2021.10.25_20.35.00"]
        + list(args_tuple),
        check=True,
    )


@click.command()
@click.option("-s", "--size", default=512, help="size in bytes")
@click.option(
    "-t",
    "--tag",
    default="{:%Y_%m_%d_%H_%M_%S}".format(datetime.now()),
    help="size in bytes",
)
def gen_rtl(size, tag):
    design = f"DFFRAM_RTL_{size}"

    designs_folder = "designs"

    design_folder = f"{designs_folder}/{design}"

    ensure_dir(design_folder)

    design_folder_containerized = f"/mnt/dffram/rtl/{designs_folder}/{design}"

    templates_dir = os.path.join(os.path.dirname(__file__), "templates")

    templates = [os.path.join(templates_dir, t) for t in os.listdir(templates_dir)]

    lookup = TemplateLookup(directories=[templates_dir], strict_undefined=True)

    for template in templates:
        basename = os.path.basename(template)
        basename_output = basename.replace(".tpl", "")
        output_path = os.path.join(design_folder, basename_output)
        template = lookup.get_template(basename)
        output = template.render(design=design, size=int(size))
        with open(output_path, "w") as f:
            f.write(output)

    openlane(
        "tclsh",
        "flow.tcl",
        "-design",
        design_folder_containerized,
        "-tag",
        tag,
        "-src",
        f"{design_folder_containerized}/dffram.v",
        "-config_file",
        f"{design_folder_containerized}/config.tcl",
    )


def main():
    try:
        gen_rtl()
    except Exception:
        print("An unhandled exception has occurred.", traceback.format_exc())
        exit(os.EX_UNAVAILABLE)


if __name__ == "__main__":
    main()
