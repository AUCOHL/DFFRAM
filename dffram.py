#!/usr/bin/env python3
# -*- coding: utf8 -*-
# Copyright ©2020-2022 The American University in Cairo
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

try:
    import click
    import yaml
    import volare
except ImportError:
    print(
        "You need to install dependencies: pip3 install --user --upgrade --no-cache-dir -r ./requirements.txt"
    )
    exit(os.EX_CONFIG)

import re
import uuid
import math
import time
import shutil
import fnmatch
import pathlib
import traceback
import subprocess

from scripts.python import sky130_hd_hack


def rp(path):
    return os.path.realpath(path)


def ensure_dir(path):
    return pathlib.Path(path).mkdir(parents=True, exist_ok=True)


# --
build_folder = ""
pdk_family = ""
pdk = ""
pdk_version = ""
scl = ""
pdk_root = ""
pdk_tech_dir = ""
pdk_ref_dir = ""
pdk_liberty_dir = ""
pdk_lef_dir = ""
pdk_tlef_dir = ""
pdk_klayout_dir = ""
pdk_magic_dir = ""
pdk_openlane_dir = ""

tool_metadata_file_path = os.path.join(os.path.dirname(__file__), "tool_metadata.yml")
tool_metadata = yaml.safe_load(open(tool_metadata_file_path).read())
openlane_version = [tool for tool in tool_metadata if tool["name"] == "openlane"][0][
    "commit"
]
openlane_image = os.getenv(
    "OPENLANE_IMAGE_NAME", default=f"efabless/openlane:{openlane_version}"
)

running_docker_ids = set()


def run_docker(image, args):
    global running_docker_ids
    global command_list
    container_id = str(uuid.uuid4())
    running_docker_ids.add(container_id)
    cmd = (
        [
            "docker",
            "run",
            "--rm",
            "--name",
            container_id,
            "-v",
            f"{pdk_root}:{pdk_root}",
            "-v",
            f"{rp('.')}:/mnt/dffram",
            "-w",
            "/mnt/dffram",
            "-e",
            f"PDK_ROOT={pdk_root}",
            "-e",
            f"PDKPATH={pdk_root}/{pdk}",
            "-e",
            f"PDK={pdk}",
            "-e",
            "PWD=/mnt/dffram",
            "-e",
            "LC_ALL=en_US.UTF-8",
            "-e",
            "LANG=en_US.UTF-8",
        ]
        + [image]
        + args
    )
    command_list.append(cmd)
    subprocess.check_call(cmd)
    running_docker_ids.remove(container_id)


openlane_scripts_path = "/openlane/scripts"
local_openlane_path = None
venv_lib_path = None


def openlane(*args_tuple):
    global no_docker_option
    args = list(args_tuple)
    if local_openlane_path is not None:
        env = os.environ.copy()
        env["PATH"] = f"{local_openlane_path}:{env['PATH']}"

        if venv_lib_path is not None:
            env["PYTHONPATH"] = venv_lib_path

        # Disable tools not typically installed in Colaboratories
        env["RUN_KLAYOUT"] = "0"
        env["RUN_CVC"] = "0"
        env["PDK_ROOT"] = pdk_root

        subprocess.check_call(args, env=env)
    else:
        run_docker(openlane_image, args)


def prep(local_pdk_root):
    global pdk, scl
    global pdk_root, pdk_tech_dir, pdk_ref_dir
    global pdk_liberty_dir, pdk_lef_dir, pdk_tlef_dir
    global pdk_klayout_dir, pdk_magic_dir, pdk_openlane_dir
    pdk_root = os.path.abspath(local_pdk_root)
    pdk_path = os.path.join(pdk_root, pdk)
    volare.enable(pdk_root=local_pdk_root, pdk=pdk_family, version=pdk_version)

    pdk_tech_dir = os.path.join(pdk_path, "libs.tech")
    pdk_ref_dir = os.path.join(pdk_path, "libs.ref")
    pdk_liberty_dir = os.path.join(pdk_ref_dir, scl, "lib")
    pdk_lef_dir = os.path.join(pdk_ref_dir, scl, "lef")
    pdk_tlef_dir = os.path.join(pdk_ref_dir, scl, "techlef")
    pdk_openlane_dir = os.path.join(pdk_tech_dir, "openlane")
    pdk_klayout_dir = os.path.join(pdk_tech_dir, "klayout")
    pdk_magic_dir = os.path.join(pdk_tech_dir, "magic")
    openlane(
        "openroad",
        "-python",
        f"{openlane_scripts_path}/mergeLef.py",
        "-i",
        f"{pdk_tlef_dir}/{scl}__nom.tlef",
        f"{pdk_lef_dir}/{scl}.lef",
        "-o",
        f"{build_folder}/merged.lef",
    )


command_list = []


def cl():
    with open("./command_list.log", "w") as f:
        f.write("\n".join([" ".join(cmd) for cmd in command_list]))


# Not true synthesis, just elaboration.
def synthesis(
    design,
    building_blocks,
    block_deinitions,
    sta_info,
    widths_supported,
    word_width_bytes,
    out_file,
    word_width,
    blocks,
):
    print("--- Synthesis ---")
    chparam = ""
    if len(widths_supported) > 1:
        if blocks == "rf":
            chparam = "catch { chparam -set WSIZE %i %s }" % (word_width, design)
        else:
            chparam = "catch { chparam -set WSIZE %i %s }" % (word_width_bytes, design)
    with open(f"{build_folder}/synth.tcl", "w") as f:
        print(design)
        f.write(
            f"""
            yosys -import
            set SCL {pdk_liberty_dir}/{sta_info["libs"]["typical"]}
            read_liberty -lib -ignore_miss_dir -setattr blackbox $SCL
            read_verilog {block_deinitions}
            read_verilog {building_blocks}
            {chparam}
            hierarchy -check -top {design}
            synth -flatten
            yosys rename -top {design}
            opt_clean -purge
            splitnets
            opt_clean -purge
            write_verilog -noattr -noexpr -nodec {out_file}
            stat -top {design} -liberty $SCL
            exit
            """
        )

    openlane("yosys", f"{build_folder}/synth.tcl")


full_width = 0
full_height = 0


def floorplan(
    design,
    sta_info,
    wmargin,
    hmargin,
    width,
    height,
    in_file,
    out_file,
    min_height,
    min_height_flag,
    site_height,
):
    global full_width, full_height
    print("--- Floorplan ---")
    full_width = width + (wmargin * 2)
    full_height = height + (hmargin * 2)

    wpm = width + wmargin
    hpm = height + hmargin

    track_file = f"{build_folder}/tracks.tcl"

    if min_height_flag:
        full_width = width + (wmargin * 2)
        full_height = min_height + (hmargin * 2)
        hmargin = full_height / 2 - height / 2
        hmargin = math.ceil(hmargin / site_height) * site_height
        hpm = height + hmargin

    with open(f"{build_folder}/fp_init.tcl", "w") as f:
        f.write(
            f"""
            read_liberty {pdk_liberty_dir}/{sta_info["libs"]["typical"]}
            read_lef {build_folder}/merged.lef
            read_verilog {in_file}
            link_design {design}
            initialize_floorplan\\
                -die_area "0 0 {full_width} {full_height}"\\
                -core_area "{wmargin} {hmargin} {wpm} {hpm}"\\
                -site unithd
            source {track_file}
            write_db {out_file}
            """
        )

    with open(f"{build_folder}/fp_init.sh", "w") as f:
        f.write(
            f"""
            set -e

            python3 {openlane_scripts_path}/new_tracks.py -i {pdk_openlane_dir}/{scl}/tracks.info -o {track_file}
            openroad -exit {build_folder}/fp_init.tcl
            """
        )

    openlane("bash", f"{build_folder}/fp_init.sh")


def placeram(
    in_file,
    out_file,
    size,
    building_blocks,
    dimensions=os.devnull,
    density=os.devnull,
    represent=os.devnull,
):
    print("--- placeRAM Script ---")
    openlane(
        "openroad",
        "-python",
        "-m",
        "placeram",
        "--output",
        out_file,
        "--size",
        size,
        "--write-dimensions",
        dimensions,
        "--write-density",
        density,
        "--represent",
        represent,
        "--building-blocks",
        building_blocks,
        in_file,
    )


def place_pins(design, sta_info, in_file, out_file, pin_order_file):
    print("--- Pin Placement ---")
    print(in_file)
    openlane(
        "openroad",
        "-python",
        f"{openlane_scripts_path}/odbpy/io_place.py",
        "--config",
        pin_order_file,
        "--input-lef",
        f"{build_folder}/merged.lef",
        "--hor-layer",
        "met3",
        "--ver-layer",
        "met2",
        "--ver-width-mult",
        "2",
        "--hor-width-mult",
        "2",
        "--hor-extension",
        "0",
        "--ver-extension",
        "0",
        "--length",
        "2",
        "-o",
        out_file,
        in_file,
    )


def verify_placement(design, sta_info, in_file):
    print("--- Verify ---")
    with open(f"{build_folder}/verify.tcl", "w") as f:
        f.write(
            f"""
            read_db {in_file}
            read_liberty {pdk_liberty_dir}/{sta_info["libs"]["typical"]}
            if {{[catch check_placement -verbose]}} {{
                puts "Placement failed: Check placement returned a nonzero value."
                exit 65
            }}
            puts "Placement successful."
            """
        )
    openlane("openroad", "-exit", f"{build_folder}/verify.tcl")


def openlane_harden(
    design,
    clock_period,
    final_netlist,
    final_placement,
    products_path,
    sta_info,
    routing_threads,
):
    print("--- Hardening With OpenLane ---")
    design_ol_dir = f"{build_folder}/openlane"
    ensure_dir(design_ol_dir)

    netlist_basename = os.path.basename(final_netlist)
    current_netlist = f"{design_ol_dir}/{netlist_basename}"
    shutil.copy(final_netlist, current_netlist)

    placement_basename = os.path.basename(final_placement)
    current_odb = f"{design_ol_dir}/{placement_basename}"
    shutil.copy(final_placement, current_odb)

    shutil.copy(
        "./scripts/openlane/interactive.tcl", f"{design_ol_dir}/interactive.tcl"
    )

    if pdk == "sky130A":
        sky130_hd_hack.process_lefs(
            lef=f"{pdk_lef_dir}/{scl}.lef",
            output_cells=f"{design_ol_dir}/cells.lef",
        )
    else:
        shutil.copy(f"{pdk_lef_dir}/{scl}.lef", f"{design_ol_dir}/cells.lef")

    with open(f"{design_ol_dir}/config.tcl", "w") as f:
        f.write(
            f"""
            set ::env(DESIGN_NAME) "{design}"

            set ::env(CLOCK_PORT) "CLK"
            set ::env(CLOCK_PERIOD) "{clock_period}"

            set ::env(LEC_ENABLE) "1"
            set ::env(FP_WELLTAP_CELL) "sky130_fd_sc_hd__tap*"

            set ::env(CELL_PAD) "0"
            set ::env(FILL_INSERTION) "0"
            set ::env(PL_RESIZER_DESIGN_OPTIMIZATIONS) "0"
            set ::env(PL_RESIZER_TIMING_OPTIMIZATIONS) "0"
            set ::env(GLB_RESIZER_DESIGN_OPTIMIZATIONS) "0"
            set ::env(GLB_RESIZER_TIMING_OPTIMIZATIONS) "0"

            set ::env(RT_MAX_LAYER) "met4"
            set ::env(GRT_ALLOW_CONGESTION) "1"

            set ::env(CELLS_LEF) "$::env(DESIGN_DIR)/cells.lef"

            set ::env(DIE_AREA) "0 0 {full_width} {full_height}"

            set ::env(DIODE_INSERTION_STRATEGY) {0}

            set ::env(ROUTING_CORES) {routing_threads}

            set ::env(DESIGN_IS_CORE) "0"
            set ::env(FP_PDN_CORE_RING) "0"

            set ::env(PRODUCTS_PATH) "{products_path}"

            set ::env(INITIAL_NETLIST) "$::env(DESIGN_DIR)/{netlist_basename}"
            set ::env(INITIAL_ODB) "$::env(DESIGN_DIR)/{placement_basename}"
            set ::env(INITIAL_SDC) "$::env(BASE_SDC_FILE)"

            set ::env(LVS_CONNECT_BY_LABEL) "1"

            set ::env(SYNTH_DRIVING_CELL) "{sta_info["driving_cell"]["name"]}"
            set ::env(SYNTH_DRIVING_CELL_PIN) "{sta_info["driving_cell"]["pin"]}"
            set ::env(IO_PCT) "0.25"
            """
        )

    openlane(
        "flow.tcl",
        "-ignore_mismatches",
        "-design",
        design_ol_dir,
        "-it",
        "-file",
        f"{design_ol_dir}/interactive.tcl",
    )


@click.command()
# Execution Flow
@click.option("-f", "--from", "frm", default="synthesis", help="Start from this step")
@click.option("-t", "--to", default="gds", help="End after this step")
@click.option(
    "--only", default=None, help="Only execute these semicolon;delimited;steps"
)
@click.option("--skip", default=None, help="Skip these semicolon;delimited;steps")

# Configuration
@click.option(
    "-p",
    "--pdk-root",
    required=False,
    default="./pdks",
    help="Optionally override the used PDK root",
)
@click.option("-O", "--output-dir", default="./build", help="Output directory.")
@click.option(
    "-b",
    "--building-blocks",
    default="sky130A:sky130_fd_sc_hd:ram",
    help="Format {pdk}:{scl}:{name} : ID of the building blocks to use.",
)
@click.option(
    "-v", "--variant", default=None, help="Use design variants (such as 1RW1R)"
)
@click.option("-s", "--size", required=True, help="Size")
@click.option(
    "-C",
    "--clock-period",
    "default_clock_period",
    default=20,
    type=float,
    help="Fallback clock period for STA (when unspecified)",
)
@click.option("--halo", default=2.5, type=float, help="Halo in microns")
@click.option(
    "--horizontal-halo",
    default=0.0,
    type=float,
    help="Horizontal halo in microns (overrides generic halo)",
)
@click.option(
    "--vertical-halo",
    default=0.0,
    type=float,
    help="Vertical halo in microns (overrides generic halo)",
)
@click.option(
    "-H", "--min-height", default=0.0, type=float, help="Die Area Height in microns"
)
@click.option(
    "-j",
    "--routing-threads",
    type=int,
    default=int(os.getenv("ROUTING_CORES") or "1"),
    help="Number of threads to be used in routing",
)

# Enable/Disable
@click.option(
    "--klayout/--no-klayout",
    default=False,
    help="Open the last def in Klayout. (Default: False)",
)
@click.option(
    "--using-local-openlane",
    default=None,
    type=str,
    help="Use this local OpenLane installation instead of a Dockerized installation.",
)
def flow(
    frm,
    to,
    only,
    pdk_root,
    skip,
    size,
    building_blocks,
    default_clock_period,
    halo,
    horizontal_halo,
    vertical_halo,
    variant,
    routing_threads,
    klayout,
    output_dir,
    min_height,
    using_local_openlane,
):
    global build_folder
    global pdk_family, pdk, pdk_version, scl
    global local_openlane_path
    global openlane_scripts_path
    global venv_lib_path

    if horizontal_halo == 0.0:
        horizontal_halo = halo

    if vertical_halo == 0.0:
        vertical_halo = halo

    if variant == "DEFAULT":
        variant = None

    local_openlane_path = using_local_openlane
    if local_openlane_path is not None:
        openlane_scripts_path = os.path.join(local_openlane_path, "scripts")
        if not os.getenv("NO_CHECK_INSTALL") == "1":
            install_path = os.path.join(local_openlane_path, "install")
            if not os.path.isdir(install_path):
                print(f"Error: OpenLane installation not found at {install_path}.")
                exit(os.EX_CONFIG)

            venv_lib = f"{local_openlane_path}/install/venv/lib"
            venv_lib_vers = os.listdir(venv_lib)
            if len(venv_lib_vers) < 1:
                print("Installation venv contains no packages.")
                exit(os.EX_CONFIG)

            venv_lib_path = os.path.join(venv_lib, venv_lib_vers[0], "site-packages")

    pdk, scl, blocks = building_blocks.split(":")
    pdk = pdk or "sky130A"
    scl = scl or "sky130_fd_sc_hd"
    blocks = blocks or "ram"
    platform = f"{pdk}:{scl}"
    building_blocks = f"{platform}:{blocks}"

    process_data_file = os.path.join(".", "platforms", pdk, "process_data.yml")
    process_data = yaml.safe_load(open(process_data_file))
    pdk_family = process_data["volare_pdk_family"]
    pdk_version = process_data["volare_pdk_version"]

    bb_dir = os.path.join(".", "models", blocks)
    if not os.path.isdir(bb_dir):
        print(f"Generic building blocks {blocks} not found.")
        exit(os.EX_NOINPUT)

    pdk_dir = os.path.join(".", "platforms", pdk, scl)
    if not os.path.isdir(pdk_dir):
        print(f"Definitions for platform {platform} not found.")
        exit(os.EX_NOINPUT)

    block_definitions_used = os.path.join(pdk_dir, "block_definitions.v")

    bb_used = os.path.join(bb_dir, "model.v")
    config_file = os.path.join(bb_dir, "config.yml")
    config = yaml.safe_load(open(config_file))

    pin_order_file = os.path.join(bb_dir, "pin_order.cfg")

    m = re.match(r"(\d+)x(\d+)", size)
    if m is None:
        print("Invalid RAM size '%s'." % size)
        exit(os.EX_USAGE)

    words = int(m[1])
    word_width = int(m[2])
    word_width_bytes = word_width / 8

    if os.getenv("FORCE_ACCEPT_SIZE") is None:
        if words not in config["counts"] or word_width not in config["widths"]:
            print("Size %s not supported by %s." % (size, building_blocks))
            exit(os.EX_USAGE)

        if variant not in config["variants"]:
            print("Variant %s is unsupported by %s." % (variant, building_blocks))
            exit(os.EX_USAGE)

    wmargin, hmargin = (horizontal_halo, vertical_halo)  # Microns

    variant_string = ("_%s" % variant) if variant is not None else ""
    design_name_template = config["design_name_template"]
    design = os.getenv("FORCE_DESIGN_NAME") or design_name_template.format(
        **{
            "count": words,
            "width": word_width,
            "width_bytes": word_width_bytes,
            "variant": variant_string,
        }
    )
    build_folder = f"{output_dir}/{size}_{variant or 'DEFAULT'}"

    tech_info_path = os.path.join(".", "platforms", pdk, scl, "tech.yml")
    tech_info = yaml.safe_load(open(tech_info_path))

    clock_period = default_clock_period
    block_clock_periods = tech_info["sta"]["clock_periods"].get(blocks)
    if block_clock_periods is not None:
        for wildcard, period in block_clock_periods.items():
            if fnmatch.fnmatch(size, wildcard):
                clock_period = period
                break

    site_info = tech_info.get("site")  # Normalize margins in terms of minimum units
    if site_info is not None:
        site_width = site_info["width"]
        site_height = site_info["height"]

        wmargin = math.ceil(wmargin / site_width) * site_width
        hmargin = math.ceil(hmargin / site_height) * site_height
    else:
        if horizontal_halo != 0.0 or vertical_halo != 0.0:
            print(
                "Note: This platform does not have site information. The halo will not be rounded up to the nearest number of sites. This may cause off-by-one issues with some tools."
            )

    sta_info = tech_info.get("sta")

    ensure_dir(build_folder)

    def i(ext=""):
        return f"{build_folder}/{design}{ext}"

    prep(pdk_root)

    start = time.time()

    netlist = i(".nl.v")
    dimensions_file = i(".dimensions.txt")
    density_file = i(".density.txt")
    initial_floorplan = i(".initfp.odb")
    initial_placement = i(".initp.odb")
    final_floorplan = i(".fp.odb")
    no_pins_placement = i(".npp.odb")
    final_placement = i(".placed.odb")

    products = f"{build_folder}/products"

    ensure_dir(products)

    width, height = 20000, 20000

    def placement(in_width, in_height):
        nonlocal width, height, hmargin, wmargin
        min_height_flag = False
        floorplan(
            design,
            sta_info,
            wmargin,
            hmargin,
            in_width,
            in_height,
            netlist,
            initial_floorplan,
            min_height,
            min_height_flag,
            site_height,
        )
        placeram(
            initial_floorplan,
            initial_placement,
            size,
            building_blocks,
            dimensions=dimensions_file,
        )
        width, height = map(lambda x: float(x), open(dimensions_file).read().split("x"))
        if height < min_height:
            min_height_flag = True

        floorplan(
            design,
            sta_info,
            wmargin,
            hmargin,
            width,
            height,
            netlist,
            final_floorplan,
            min_height,
            min_height_flag,
            site_height,
        )
        placeram(
            final_floorplan,
            no_pins_placement,
            size,
            building_blocks,
            density=density_file,
        )
        place_pins(design, sta_info, no_pins_placement, final_placement, pin_order_file)
        verify_placement(design, sta_info, final_placement)

    steps = [
        (
            "synthesis",
            lambda: synthesis(
                design,
                bb_used,
                block_definitions_used,
                sta_info,
                config["widths"],
                word_width_bytes,
                netlist,
                word_width,
                blocks,
            ),
        ),
        ("placement", lambda: placement(width, height)),
        (
            "openlane_harden",
            lambda: openlane_harden(
                design,
                clock_period,
                netlist,
                final_placement,
                products,
                sta_info,
                routing_threads,
            ),
        ),
    ]

    only = only.split(";") if only is not None else None
    skip = skip.split(";") if skip is not None else []

    execute_steps = False
    for step in steps:
        name, action = step
        if frm == name:
            execute_steps = True
        if execute_steps:
            if (only is None or name in only) and (name not in skip):
                try:
                    action()
                except KeyboardInterrupt as e:
                    print("\n\nStopping on keyboard interrupt...")
                    print("Killing docker containers...")
                    for id in running_docker_ids:
                        subprocess.call(["docker", "kill", id])
                    raise e
        if to == name:
            execute_steps = False

    elapsed = time.time() - start

    print("Done in %.2fs." % elapsed)
    cl()


def main():
    try:
        flow()
    except subprocess.CalledProcessError as e:
        print("A step has failed:", e)
        print(f"Quick invoke: {' '.join(e.cmd)}")
        cl()
        exit(os.EX_UNAVAILABLE)
    except Exception:
        print("An unhandled exception has occurred.", traceback.format_exc())
        cl()
        exit(os.EX_UNAVAILABLE)


if __name__ == "__main__":
    main()
