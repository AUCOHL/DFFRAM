#!/usr/bin/env python3
# -*- coding: utf8 -*-
# Copyright ©2020-2021 The American University in Cairo
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
