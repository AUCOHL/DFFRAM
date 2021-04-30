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

def rp(path):
    return os.path.realpath(path)

def ensure_dir(path):
    return pathlib.Path(path).mkdir(parents=True, exist_ok=True)

def run_docker(image, args, interactive=False):
    subprocess.run([
        "docker", "run",
        "-tiv" if interactive else "-v",
        "%s:/mnt/dffram" % rp(".."),
        "-w", "/mnt/dffram/Compiler",
    ] + [image] + args, check=True)

def openlane(*args_tuple, interactive=False):
    args = list(args_tuple)
    run_docker("efabless/openlane", args)

def STA(build_folder, design, netlist, spef_file):
    print("--- Static Timing Analysis ---")
    with open("%s/sta.tcl" % build_folder, 'w') as f:
        env_vars = """
            set ::env(SYNTH_DRIVING_CELL) "sky130_fd_sc_hd__inv_8"
            set ::env(SYNTH_DRIVING_CELL_PIN) "Y"
            set ::env(SYNTH_CAP_LOAD) "17.65"
            set ::env(IO_PCT) 0.2
            set ::env(SYNTH_MAX_FANOUT) 5
            set ::env(CLOCK_PORT) "CLK"
            set ::env(CLOCK_PERIOD) "3"
            set ::env(LIB_FASTEST) ./example_support/sky130_fd_sc_hd__ff_n40C_1v95.lib
            set ::env(LIB_SLOWEST) ./example_support/sky130_fd_sc_hd__ss_100C_1v60.lib
            set ::env(CURRENT_NETLIST) {netlist}
            set ::env(DESIGN_NAME) {design}
            set ::env(BASE_SDC_FILE) /openLANE_flow/scripts/base.sdc
            source "/openLANE_flow/scripts/sta.tcl"

        """.format(
            build_folder=build_folder,
            design=design,
            netlist=netlist)
        if spef_file:
            env_vars =\
                    """
                    set ::env(CURRENT_SPEF) {spef_file}
                    set ::env(opensta_report_file_tag) {spef_file}.sta
                    """.format(spef_file=spef_file) + env_vars
        else:
            env_vars =\
                    """
                    set ::env(opensta_report_file_tag) {netlist}.sta
                    """.format(netlist=netlist) + env_vars
        f.write(env_vars)
    openlane("sta", "%s/sta.tcl" % build_folder)

bb_used = "BB.v"
# Not true synthesis, just elaboration.
def synthesis(build_folder, design, word_length_bytes, out_file):
    print("--- Synthesis ---")
    chparam = ""
    if word_length_bytes is not None:
        chparam = "chparam -set SIZE %i %s" % (word_length_bytes, design)
    with open("%s/synth.tcl" % build_folder, 'w') as f:
        f.write("""
        yosys -import
        set vtop {design}
        set SCL $env(LIBERTY)
        read_liberty -lib -ignore_miss_dir -setattr blackbox $SCL
        read_verilog {bb_used}
        {chparam}
        hierarchy -check -top {design}
        synth -top {design} -flatten
        opt_clean -purge
        splitnets
        opt_clean -purge
        write_verilog -noattr -noexpr -nodec {out_file}
        stat -top {design} -liberty $SCL
        exit
        """.format(design=design, out_file=out_file, bb_used=bb_used, chparam=chparam))

    with open("%s/synth.sh" % build_folder, 'w') as f:
        f.write("""
        export LIBERTY=./example_support/sky130_fd_sc_hd__tt_025C_1v80.lib
        yosys %s/synth.tcl
        """ % build_folder)

    openlane("bash", "%s/synth.sh" % build_folder)

    STA(build_folder, design, out_file, None)

def floorplan(build_folder, design, margin, width, height, in_file, out_file):
    print("--- Floorplan ---")
    full_width = width + margin
    full_height = height + margin
    with open("%s/fp_init.tcl" % build_folder, 'w') as f:
        f.write("""
        read_liberty ./example_support/sky130_fd_sc_hd__tt_025C_1v80.lib
        read_lef ./example_support/sky130_fd_sc_hd.merged.lef
        read_verilog {in_file}
        link_design {design}
        initialize_floorplan\
            -die_area "0 0 {full_width} {full_height}"\
            -core_area "{margin} {margin} {width} {height}"\
            -site unithd\
            -tracks ./example_support/sky130hd.tracks
        write_def {out_file}
        """.format(
            design=design,
            margin=margin,
            width=width,
            full_width=full_width,
            height=height,
            full_height=full_height,
            in_file=in_file,
            out_file=out_file
        ))

    openlane("openroad", "%s/fp_init.tcl" % build_folder)


def placeram(in_file, out_file, size, experimental=False, dimensions=os.devnull, represent=os.devnull):
    print("--- placeRAM Script ---")
    unaltered = out_file + ".ref"

    run_docker("cloudv/dffram-env", [
        "python3", "-m", "placeram",
        "--output", unaltered,
        "--lef", "./example_support/sky130_fd_sc_hd.lef",
        "--tech-lef", "./example_support/sky130_fd_sc_hd.tlef",
        "--size", size,
        "--write-dimensions", dimensions,
        "--represent", represent
    ] + (["--experimental"] if experimental else []) + [
        in_file
    ])

    unaltered_str = open(unaltered).read()

    altered_str = re.sub(r"\+ PORT", "", unaltered_str)

    with open(out_file, 'w') as f:
        f.write(altered_str)

def place_pins(in_file, out_file):
    print("--- Pin Placement ---")
    openlane(
        "python3",
        "/openLANE_flow/scripts/io_place.py",
        "--input-lef", "./example_support/sky130_fd_sc_hd.merged.lef",
        "--input-def", in_file,
        "--config", "./pin_order.cfg",
        "--hor-layer", "4",
        "--ver-layer", "3",
        "--ver-width-mult", "2",
        "--hor-width-mult", "2",
        "--hor-extension", "-1",
        "--ver-extension", "-1",
        "--length", "2",
        "-o", out_file
    )


def verify_placement(build_folder, in_file):
    print("--- Verify ---")
    with open("%s/verify.tcl" % build_folder, 'w') as f:
        f.write("""
        read_liberty ./example_support/sky130_fd_sc_hd__tt_025C_1v80.lib
        read_lef ./example_support/sky130_fd_sc_hd.merged.lef
        read_def {in_file}
        if [check_placement -verbose] {{
            puts "Placement failed: Check placement returned a nonzero value."
            exit 65
        }}
        puts "Placement successful."
        """.format(in_file=in_file))

    openlane("openroad", "%s/verify.tcl" % build_folder)

def pdngen(build_folder, width, height, in_file, out_file):
    print("--- Power Distribution Network Construction ---")
    pitch = 50 # temp: till we arrive at a function that takes in width
    offset = 25 # temp: till we arrive at a function that takes in width
    pdn_cfg = """

    set ::halo 0
    # POWER or GROUND #Std. cell rails starting with power or ground rails at the bottom of the core area
    set ::rails_start_with "POWER" ;

    # POWER or GROUND #Upper metal stripes starting with power or ground rails at the left/bottom of the core area
    set ::stripes_start_with "POWER" ;

    set ::power_nets "VPWR";
    set ::ground_nets "VGND";

    set pdngen::global_connections {{
      VPWR {{
        {{inst_name .* pin_name VPWR}}
        {{inst_name .* pin_name VPB}}
      }}
      VGND {{
        {{inst_name .* pin_name VGND}}
        {{inst_name .* pin_name VNB}}
      }}
    }}

    pdngen::specify_grid stdcell {{
        name grid
        rails {{
            met1 {{width 0.17 pitch 2.7 offset 0}}
        }}
        straps {{
            met4 {{width 1.6 pitch {pitch} offset {offset}}}
        }}
        connect {{
        {{ met1 met4 }}
        }}
    }}
    """.format(pitch=pitch, offset=offset)

    pdn_cfg_file = "%s/pdn.cfg" % build_folder
    with open(pdn_cfg_file, 'w') as f:
        f.write(pdn_cfg)

    pdn_tcl = """

        read_lef ./example_support/sky130_fd_sc_hd.merged.lef

        read_def {in_file}

        pdngen {cfg_file} -verbose

        write_def {out_file}
        """.format(cfg_file=pdn_cfg_file,
                in_file=in_file,
                out_file=out_file)

    with open("%s/pdn.tcl" % build_folder, 'w') as f:
        f.write(pdn_tcl)
    openlane("openroad", "%s/pdn.tcl" % build_folder)

def obs_route(build_folder, metal_layer, width, height, in_file, out_file):
    print("--- Routing Obstruction Creation---")
    openlane(
        "python3",
        "/openLANE_flow/scripts/add_def_obstructions.py",
        "--lef", "./example_support/sky130_fd_sc_hd.merged.lef",
        "--input-def", in_file,
        "--obstructions",
        "met{metal_layer} 0 0 {width} {height}".format(metal_layer=metal_layer,
            width=width,
            height=height),
        "--output", out_file)

def route(build_folder, in_file, out_file):
    print("--- Route ---")
    global_route_guide = "%s/gr.guide" % build_folder
    with open("%s/tr.param" % build_folder, 'w') as f:
        # We use textwrap.dedent because tr.params does not take kindly to whitespace, at all
        f.write(textwrap.dedent("""\
        lef:./example_support/sky130_fd_sc_hd.merged.lef
        def:{in_file}
        output:{out_file}
        guide:{global_route_guide}
        outputguide:{build_folder}/dr.guide
        outputDRC:{build_folder}/drc
        threads:8
        verbose:1
        """.format(in_file=in_file, out_file=out_file, global_route_guide=global_route_guide, build_folder=build_folder)))

    with open("%s/route.tcl" % build_folder, 'w') as f:
        f.write("""
        source ./example_support/sky130hd.vars
        read_liberty ./example_support/sky130_fd_sc_hd__tt_025C_1v80.lib
        read_lef ./example_support/sky130_fd_sc_hd.merged.lef
        read_def {in_file}
        global_route \\
            -guide_file {global_route_guide} \\
            -layers $global_routing_layers \\
            -clock_layers $global_routing_clock_layers \\
            -unidirectional_routing \\
            -overflow_iterations 100
        tr::detailed_route_cmd {build_folder}/tr.param
        """.format(in_file=in_file, global_route_guide=global_route_guide, build_folder=build_folder))

    openlane("openroad", "%s/route.tcl" % build_folder)

def SPEF_extract(build_folder, def_file, spef_file=None):
    print("--- Extract SPEF ---")
    openlane("python3", "/openLANE_flow/scripts/spef_extractor/main.py",
            "--def_file", def_file,
            "--lef_file", "./example_support/sky130_fd_sc_hd.merged.lef",
            "--wire_model", "L",
            "--edge_cap_factor", "1")

def add_pwr_gnd_pins(build_folder, original_netlist,
        def_file, intermediate_file, out_file1,
        out_file2):
    print("--- Adding power and ground pins to netlist ---")

    openlane("python3", "/openLANE_flow/scripts/write_powered_def.py",
            "-d", def_file,
            "-l", "./example_support/sky130_fd_sc_hd.merged.lef",
            "--power-port", "VPWR",
            "--ground-port", "VGND",
            "-o", intermediate_file)

    with open("%s/write_pwr_gnd_verilog.tcl" % build_folder, "w") as f:
        f.write("""
        read_lef ./example_support/sky130_fd_sc_hd.merged.lef
        read_def {def_file}
        read_verilog {netlist}
        puts "Writing the modified nl.v "
        puts "writing file"
        puts {out_file}
        write_verilog -include_pwr_gnd {out_file}
        """.format(netlist=original_netlist, def_file=intermediate_file,
            out_file=out_file1))

    openlane("openroad",
            "%s/write_pwr_gnd_verilog.tcl" % build_folder)

    with open("%s/rewrite_netlist.tcl" % build_folder, 'w') as f:
        f.write("""
        yosys -import
        read_verilog {verilog_file}; # usually from openroad
        write_verilog -noattr -noexpr -nohex -nodec {out_file};
        """.format(verilog_file=out_file1, out_file=out_file2))

    openlane("yosys",
            "-c", "%s/rewrite_netlist.tcl" % build_folder)


def write_RAM_LEF(build_folder, design, in_file, out_file):
    print("--- Write LEF view of the RAM Module ---")
    with open("%s/write_lef.tcl" % build_folder, "w") as f:
        f.write("""
        puts "Running magic script…"
        lef read ./example_support/sky130_fd_sc_hd.merged.lef
        def read {in_file}
        load {design} -dereference
        lef write {out_file}
        """.format(design=design,
            in_file=in_file,
            out_file=out_file))

    openlane("magic",
            "-dnull",
            "-noconsole",
            "-rcfile",
            "./example_support/sky130A.magicrc",
            "%s/write_lef.tcl" % build_folder)

def write_RAM_LIB(build_folder, design, netlist, libfile):
    openlane("perl",
            "./scripts/perl/verilog_to_lib.pl",
            design,
            netlist,
            libfile)


def lvs(build_folder, design, in_1, in_2, report):
    print("--- LVS ---")
    with open("%s/lvs.tcl" % build_folder, "w") as f:
        f.write("""
        puts "Running magic script…"
        lef read ./example_support/sky130_fd_sc_hd.merged.lef
        def read {in_1}
        load {design} -dereference
        extract do local
        extract no capacitance
        extract no coupling
        extract no resistance
        extract no adjust
        extract unique
        extract
        ext2spice lvs
        ext2spice
        """.format(design=design, in_1=in_1))

    with open("%s/lvs.sh" % build_folder, "w") as f:
        f.write("""
        magic -rcfile ./example_support/sky130A.magicrc -noconsole -dnull < {build_folder}/lvs.tcl
        mv *.ext *.spice {build_folder}
        netgen -batch lvs "{build_folder}/{design}.spice {design}" "{in_2} {design}" -full
        mv comp.out {report}
        """.format(build_folder=build_folder, design=design, in_1=in_1, in_2=in_2, report=report))

    openlane("bash", "%s/lvs.sh" % build_folder)

def antenna_check(build_folder, def_file, out_file):
    # using openroad antenna check
    print("--- Antenna Check ---")
    with open("%s/antenna_check.tcl" % build_folder, 'w') as f:
        f.write("""
            set ::env(REPORTS_DIR) {build_folder}
            set ::env(MERGED_LEF_UNPADDED) ./example_support/sky130_fd_sc_hd.merged.lef
            set ::env(CURRENT_DEF) {def_file}
            read_lef $::env(MERGED_LEF_UNPADDED)
            read_def -order_wires {def_file}
            check_antennas -path {build_folder}
            # source /openLANE_flow/scripts/openroad/or_antenna_check.tcl
        """.format(build_folder=build_folder,
            def_file=def_file,
            out_file=out_file))
    openlane("openroad", "%s/antenna_check.tcl" % build_folder)
    openlane("mv", "%s/antenna.rpt" % build_folder, out_file)

@click.command()
@click.option("-f", "--frm", default="synthesis", help="Start from this step")
@click.option("-t", "--to", default="lvs", help="End after this step")
@click.option("--only", default=None, help="Only execute this step")
@click.option("-s", "--size", required=True, help="Size")
@click.option("-e", "--experimental-bb", is_flag=True, default=False, help="Use BB.wip.v instead of BB.v.")
@click.option("-v", "--variant", default=None, help="Use design variants (such as 1RW1R). Experimental only.")
def flow(frm, to, only, size, experimental_bb, variant):
    global bb_used
    if experimental_bb:
        bb_used = "BB.wip.v"
    
    m = re.match(r"(\d+)x(\d+)", size)
    if m is None:
        eprint("Invalid RAM size '%s'." % size)
        exit(64)
    
    words = int(m[1])
    word_length = int(m[2])
    word_length_bytes = word_length / 8

    design = "RAM%s" % size 
    build_folder = "./build/%s" % design
    if experimental_bb:
        design = "RAM%i" % words
        if variant is not None and variant != "DEFAULT":
            design += "_" + variant
        build_folder = "./build/%s_SIZE%i" % (design, word_length)

    ensure_dir(build_folder)

    def i(ext=""):
        return "%s/%s%s" %(build_folder, design, ext)

    if not os.path.isdir("./example_support"):
        print("Untarring support files…")
        subprocess.run(["tar", "-xJf", "./example/example_support.tar.xz"])

    start = time.time()

    netlist = i(".nl.v")
    initial_floorplan = i(".initfp.def")
    initial_placement = i(".initp.def")
    dimensions_file = i(".dimensions.txt")
    final_floorplan = i(".fp.def")
    no_pins_placement = i(".npp.def")
    final_placement = i(".placed.def")
    pdn = i(".pdn.def")
    obstructed = i(".obs.def")
    routed = i(".routed.def")
    spef = i(".routed.spef")
    lef_view = i(".lef")
    lib_view = i(".lib")
    powered_def = i(".powered.def")
    norewrite_powered_netlist = i(".norewrite_powered.nl.v")
    powered_netlist = i(".powered.nl.v")
    antenna_report = i(".antenna.rpt")
    report = i(".rpt")

    try:
        width, height = map(lambda x: float(x), open(dimensions_file).read().split("x"))
        height += 3
    except Exception:
        width, height = 20000, 20000


    def placement(in_width, in_height):
        nonlocal width, height
        floorplan(build_folder, design, 5, in_width, in_height, netlist, initial_floorplan)
        placeram(initial_floorplan, initial_placement, size, experimental_bb, dimensions_file)
        width, height = map(lambda x: float(x), open(dimensions_file).read().split("x"))
        height += 3 # OR fails to create the proper amount of rows without some slack.
        floorplan(build_folder, design, 5, width, height, netlist, final_floorplan)
        placeram(final_floorplan, no_pins_placement, size, experimental_bb)
        place_pins(no_pins_placement, final_placement)
        verify_placement(build_folder, final_placement)

    steps = [
        ("synthesis", lambda: synthesis(build_folder, design, word_length_bytes if experimental_bb else None, netlist)),
        ("placement", lambda: placement(width, height)),
        ("pdngen", lambda: pdngen(build_folder, width, height, final_placement, pdn)),
        ("obs_route", lambda: obs_route(build_folder, 5, width, height, pdn,
            obstructed)),
        ("routing", lambda:(
            route(build_folder, obstructed, routed),
            SPEF_extract(build_folder, routed, spef),
            STA(build_folder, design, netlist, spef))),
        ("add_pwr_gnd_pins", lambda: add_pwr_gnd_pins(build_folder, netlist,
            routed,
            powered_def,
            norewrite_powered_netlist,
            powered_netlist)),
        ("write_lef", lambda: write_RAM_LEF(build_folder, design, routed,
            lef_view)),
        ("write_lib", lambda: write_RAM_LIB(build_folder, design,
            powered_netlist,
            lib_view)),
        ("antenna_check", lambda: antenna_check(build_folder, routed, antenna_report)),
        ("lvs", lambda: lvs(build_folder, design, routed, powered_netlist, report))
    ]

    execute_steps = False
    for step in steps:
        if frm == step[0]:
            execute_steps = True
        if execute_steps:
            if only is None or only == step[0]:
                step[1]()
        if to == step[0]:
            execute_steps = False

    elapsed = time.time() - start

    print("Done in %.2fs." % elapsed)

def main():
    try:
        flow()
    except Exception:
        print("An unhandled exception has occurred.", traceback.format_exc())
        exit(69)

if __name__ == '__main__':
    main()
