#!/usr/bin/env python3
# -*- coding: utf8 -*-
# Copyright ©2020-2023 The American University in Cairo
# Copyright ©2023 Efabless Corporation
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
import math
from typing import List
from fnmatch import fnmatch
from decimal import Decimal

import yaml
import cloup
from openlane.common import mkdirp
from openlane.config import Variable
from openlane.logging import warn, err
from openlane.state import DesignFormat
from openlane.flows import SequentialFlow, cloup_flow_opts, Flow
from openlane.steps import Yosys, OpenROAD, Magic, KLayout, Netgen, Odb, Checker, Misc


class PlaceRAM(Odb.OdbpyStep):
    id = "DFFRAM.PlaceRAM"

    config_vars = [
        Variable(
            "RAM_SIZE",
            str,
            "The size of the RAM macro being hardened the format {words}x{bits}",
        ),
        Variable(
            "BUILDING_BLOCKS",
            str,
            "The set of building blocks being used.",
            default="ram",
        ),
    ]

    def get_script_path(self):
        return "placeram"

    def get_command(self) -> List[str]:
        raw = super().get_command() + [
            "--building-blocks",
            f"{self.config['PDK']}:{self.config['STD_CELL_LIBRARY']}:{self.config['BUILDING_BLOCKS']}",
            "--size",
            self.config["RAM_SIZE"],
        ]
        raw.insert(raw.index("placeram"), "-m")
        return raw


class Floorplan(OpenROAD.Floorplan):
    id = "DFFRAM.Floorplan"

    outputs = [
        DesignFormat.ODB,
    ]

    config_vars = [
        var
        for var in OpenROAD.Floorplan.config_vars
        if var.name not in ["FP_SIZING", "CORE_AREA", "DIE_AREA"]
    ] + [
        Variable(
            "HORIZONTAL_HALO",
            type=Decimal,
            description="The space between the horizontal edges of the die area and the core area in microns.",
            units="µm",
            default=2.5,
        ),
        Variable(
            "VERTICAL_HALO",
            type=Decimal,
            description="The space between the vertical edges of the die area and the core area in microns.",
            units="µm",
            default=2.5,
        ),
        Variable(
            "MINIMUM_HEIGHT",
            type=Decimal,
            description="A minimum height to be applied",
            default=0,
            units="µm",
        ),
    ]

    def run(self, state_in, **kwargs):
        min_height = self.config["MINIMUM_HEIGHT"]

        core_width = Decimal(
            state_in.metrics.get("dffram__suggested__core_width") or 20000
        )
        core_height = Decimal(
            state_in.metrics.get("dffram__suggested__core_height") or 20000
        )

        horizontal_halo = self.config["HORIZONTAL_HALO"]
        vertical_halo = self.config["VERTICAL_HALO"]

        pdk = self.config["PDK"]
        scl = self.config["STD_CELL_LIBRARY"]

        tech_info_path = os.path.join(".", "platforms", pdk, scl, "tech.yml")
        tech_info = yaml.safe_load(open(tech_info_path))
        site_info = tech_info.get("site")

        site_width = Decimal(1)
        site_height = Decimal(1)

        if site_info is not None:
            site_width = Decimal(site_info["width"])
            site_height = Decimal(site_info["height"])

            horizontal_halo = math.ceil(horizontal_halo / site_width) * site_width
            vertical_halo = math.ceil(vertical_halo / site_height) * site_height
        else:
            if horizontal_halo != 0.0 or vertical_halo != 0.0:
                warn(
                    "Note: This platform does not have site information. The halo will not be rounded up to the nearest number of sites. This may cause off-by-one issues with some tools."
                )

        die_width = core_width + horizontal_halo * 2
        die_height = core_height + vertical_halo * 2
        if die_height < min_height:
            die_height = min_height
            vertical_halo = (die_height - core_height) / 2
            vertical_halo = math.ceil(vertical_halo / site_height) * site_height

        kwargs, env = self.extract_env(kwargs)

        env["DIE_AREA"] = f"0 0 {die_width} {die_height}"
        env[
            "CORE_AREA"
        ] = f"{horizontal_halo} {vertical_halo} {horizontal_halo + core_width} {vertical_halo + core_height}"
        env["FP_SIZING"] = "absolute"
        return super().run(state_in, env=env, **kwargs)


@Flow.factory.register()
class DFFRAM(SequentialFlow):
    Steps = [
        Yosys.Synthesis,
        Misc.LoadBaseSDC,
        OpenROAD.STAPrePNR,
        Floorplan,
        PlaceRAM,
        Floorplan,
        PlaceRAM,
        OpenROAD.IOPlacement,
        Odb.CustomIOPlacement,
        OpenROAD.GeneratePDN,
        OpenROAD.STAMidPNR,
        OpenROAD.GlobalRouting,
        OpenROAD.STAMidPNR,
        OpenROAD.DetailedRouting,
        Checker.TrDRC,
        Odb.ReportDisconnectedPins,
        Checker.DisconnectedPins,
        Odb.ReportWireLength,
        Checker.WireLength,
        OpenROAD.RCX,
        OpenROAD.STAPostPNR,
        OpenROAD.IRDropReport,
        Magic.StreamOut,
        Magic.WriteLEF,
        KLayout.StreamOut,
        KLayout.XOR,
        Checker.XOR,
        Magic.DRC,
        Checker.MagicDRC,
        Magic.SpiceExtraction,
        Checker.IllegalOverlap,
        Netgen.LVS,
        Checker.LVS,
    ]


@cloup.command()
@cloup.option("-b", "--building-blocks", default="ram")
@cloup.option(
    "-v", "--variant", default=None, help="Use design variants (such as 1RW1R)"
)
@cloup.option(
    "-C",
    "--clock-period",
    "default_clock_period",
    default=20,
    type=Decimal,
    help="Fallback clock period for STA (when unspecified by the platform)",
)
@cloup.option(
    "--horizontal-halo",
    default=2.5,
    type=Decimal,
    help="Horizontal halo in µm",
)
@cloup.option(
    "--vertical-halo",
    default=2.5,
    type=Decimal,
    help="Vertical halo in µm",
)
@cloup.option(
    "-H",
    "--min-height",
    default=0.0,
    type=Decimal,
    help="Minimum height in µm",
)
@cloup_flow_opts(accept_config_files=False)
@cloup.argument("size", default="32x32", nargs=1)
def main(
    pdk,
    scl,
    frm,
    to,
    skip,
    tag,
    last_run,
    with_initial_state,
    size,
    building_blocks,
    variant,
    horizontal_halo,
    vertical_halo,
    default_clock_period,
    min_height,
    flow_name,
    **kwargs,
):
    scl = scl or "sky130_fd_sc_hd"
    platform = f"{pdk}:{scl}"

    bb_dir = os.path.join(".", "models", building_blocks)
    if not os.path.isdir(bb_dir):
        err(f"Generic building blocks {building_blocks} not found.")
        exit(os.EX_NOINPUT)

    pdk_dir = os.path.join(".", "platforms", pdk, scl)
    if not os.path.isdir(pdk_dir):
        err(f"Definitions for platform {platform} not found.")
        exit(os.EX_NOINPUT)

    block_definitions_used = os.path.join(pdk_dir, "block_definitions.v")
    bb_used = os.path.join(bb_dir, "model.v")
    platform_config_file = os.path.join(bb_dir, "config.yml")
    platform_config = yaml.safe_load(open(platform_config_file))

    pin_order_file = os.path.join(bb_dir, "pin_order.cfg")
    m = re.match(r"(\d+)x(\d+)", size)
    if m is None:
        err(f"Invalid RAM size '{size}'.")
        exit(os.EX_USAGE)

    words = int(m[1])
    word_width = int(m[2])
    word_width_bytes = word_width // 8

    if os.getenv("FORCE_ACCEPT_SIZE") != 1:
        if (
            words not in platform_config["counts"]
            or word_width not in platform_config["widths"]
        ):
            err("Size %s not supported by %s." % (size, building_blocks))
            exit(os.EX_USAGE)

        if variant not in platform_config["variants"]:
            err("Variant %s is unsupported by %s." % (variant, building_blocks))
            exit(os.EX_USAGE)

    variant_string = ("_%s" % variant) if variant is not None else ""
    design_name_template = platform_config["design_name_template"]
    design = os.getenv("FORCE_DESIGN_NAME") or design_name_template.format(
        **{
            "count": words,
            "width": word_width,
            "width_bytes": word_width_bytes,
            "variant": variant_string,
        }
    )

    build_dir = os.path.join("build", design)
    mkdirp(build_dir)

    tech_info_path = os.path.join(".", "platforms", pdk, scl, "tech.yml")
    tech_info = yaml.safe_load(open(tech_info_path))

    clock_period = default_clock_period
    block_clock_periods = tech_info["sta"]["clock_periods"].get(building_blocks)
    if block_clock_periods is not None:
        for wildcard, period in block_clock_periods.items():
            if fnmatch(size, wildcard):
                clock_period = period
                break

    logical_width = word_width_bytes
    if building_blocks == "rf":
        logical_width = word_width

    TargetFlow = Flow.factory.get(flow_name) or DFFRAM
    dffram_flow = TargetFlow(
        {
            "DESIGN_NAME": design,
            "CLOCK_PORT": "CLK",
            "CLOCK_PERIOD": clock_period,
            "GPL_CELL_PADDING": 0,
            "DPL_CELL_PADDING": 0,
            "RT_MAX_LAYER": "met4",
            "GRT_ALLOW_CONGESTION": True,
            "PDK": pdk,
            "STD_CELL_LIBRARY": scl,
            "RAM_SIZE": size,
            "BUILDING_BLOCKS": building_blocks,
            "VERILOG_FILES": [
                block_definitions_used,
                bb_used,
            ],
            "SYNTH_ELABORATE_ONLY": True,
            "SYNTH_ELABORATE_FLATTEN": True,
            "SYNTH_READ_BLACKBOX_LIB": True,
            "SYNTH_EXCLUSION_CELL_LIST": "/dev/null",
            "SYNTH_PARAMETERS": f"WSIZE={logical_width}",
            "GRT_REPAIR_ANTENNAS": False,
            "MINIMUM_HEIGHT": min_height,
            "VERTICAL_HALO": vertical_halo,
            "HORIZONTAL_HALO": horizontal_halo,
            "CLOCK_PERIOD": clock_period,
            # IO Placement
            "FP_PIN_ORDER_CFG": pin_order_file,
            "FP_IO_VTHICKNESS_MULT": Decimal(2),
            "FP_IO_HTHICKNESS_MULT": Decimal(2),
            "FP_IO_HEXTEND": Decimal(0),
            "FP_IO_VEXTEND": Decimal(0),
            "FP_IO_VLENGTH": 2,
            "FP_IO_HLENGTH": 2,
        },
        design_dir=build_dir,
    )

    final_state = dffram_flow.start(
        frm=frm,
        to=to,
        skip=skip,
        tag=tag,
        last_run=last_run,
        with_initial_state=with_initial_state,
    )

    mkdirp("products")
    final_state.save_snapshot(
        os.path.join(
            "products",
            design,
        )
    )


if __name__ == "__main__":
    main()
