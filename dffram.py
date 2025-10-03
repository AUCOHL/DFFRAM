#!/usr/bin/env python3
# -*- coding: utf8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright ©2020-2025, The American University in Cairo
# Copyright ©2023 Efabless Corporation
import os
import re
from fnmatch import fnmatch
from decimal import Decimal

import yaml
import cloup
from librelane.common import mkdirp
from librelane.logging import err
from librelane.flows import cloup_flow_opts, Flow


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
    pdk_root,
    **kwargs,
):
    if variant == "DEFAULT":
        variant = None

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

    rt_max_layer = tech_info["metal_layers"]["rt-max-layer"]

    TargetFlow = Flow.factory.get(flow_name) or Flow.factory.get("DFFRAMFlow")
    dffram_flow = TargetFlow(
        {
            "DESIGN_NAME": design,
            "CLOCK_PORT": "CLK",
            "CLOCK_PERIOD": clock_period,
            "GPL_CELL_PADDING": 0,
            "DPL_CELL_PADDING": 0,
            "RT_MAX_LAYER": rt_max_layer,
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
            "SYNTH_PARAMETERS": [f"WSIZE={logical_width}"],
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
            # PDN
            "FP_PDN_MULTILAYER": False,
        },
        design_dir=os.path.abspath(build_dir),
        pdk_root=pdk_root,
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
