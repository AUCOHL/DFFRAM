#!/usr/bin/env python3
# -*- coding: utf8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright ©2020-2022, The American University in Cairo
import gdstk

import subprocess
import pathlib

subprocess.check_call(["mkdir", "-p", "images"])

gds_files = list(pathlib.Path("build").glob("**/gds/*.gds"))
for file in gds_files:
    size = file.parts[1]
    size = size.split("_")[0]
    height, width = size.split("x")
    height = int(height) * 250
    svg = f"images/{size}.svg"
    png = f"images/{size}.png"
    print(file, size)
    library = gdstk.read_gds(file)
    top_cells = library.top_level()
    top_cells[0].write_svg(svg)
    subprocess.check_call(["rsvg-convert", "-h", str(height), "-o", png, svg])
