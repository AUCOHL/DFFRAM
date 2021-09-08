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
import pya

app = pya.Application.instance()

try:
    win = app.main_window()

    layout = os.getenv("LAYOUT")

    tech = pya.Technology()

    tech.load("/usr/local/pdk/sky130A/libs.tech/klayout/sky130A.lyt")

    layout_options = tech.load_layout_options

    layout_options.keep_other_cells = True

    extra_lefs = ["./build/32x32_DEFAULT/merged.lef"]
    extra_lefs = [os.path.abspath(p) for p in extra_lefs]

    layout_options.lefdef_config.lef_files = extra_lefs

    cell_view = win.load_layout(layout, layout_options, 0)
    

except Exception as e:
    print(e)
    app.exit(-1)