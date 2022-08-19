#!/usr/bin/env -S klayout -rm

# UNDER CONSTRUCTION

# Adapted from OpenLane by Donn.
# For use with Klayout only.

# Copyright 2020 Efabless Corporation
# Copyright 2021 The American University in Cairo and the Cloud V Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import pya

app = pya.Application.instance()

try:
    win = app.main_window()

    pdk_root = os.getenv("PDK_ROOT")
    if pdk_root is None:
        raise Exception("PDK_ROOT environment variable is not set.")

    pdk_name = os.getenv("PDK")
    if pdk_name is None:
        raise Exception("PDK environment variable is not set.")

    layout = os.getenv("LAYOUT")
    if layout is None:
        raise Exception("LAYOUT environment variable is not set.")

    # Relative to the layout path (or absolute), ':' delimited. Required.
    lef_files = os.getenv("LEF_FILES")
    if layout is None:
        raise Exception("LEF_FILES environment variable is not set.")

    tech_file_path = os.getenv("KLAYOUT_TECH") or os.path.join(
        pdk_root, pdk_name, "libs.tech", "klayout", "tech", f"{pdk_name}.lyt"
    )

    tech = pya.Technology()
    tech.load(tech_file_path)

    layout_options = tech.load_layout_options

    layout_options.keep_other_cells = True

    layout_options = tech.load_layout_options
    layout_options.lefdef_config.macro_resolution_mode = 1
    layout_options.lefdef_config.read_lef_with_def = False
    layout_options.lefdef_config.lef_files = lef_files.split(":")

    cell_view = win.load_layout(layout, layout_options, 0)

except Exception as e:
    print(e, file=sys.stderr)
    app.exit(-1)
