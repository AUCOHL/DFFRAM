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
import sys
import math
import time
import yaml
import pathlib
import textwrap
import traceback
import subprocess

pdk_tech_dir = ""
pdk_ref_dir = ""
pdk_liberty_dir = ""
pdk_lef_dir = ""
pdk_tlef_dir = ""
pdk_klayout_dir = ""
pdk_magic_dir = ""
pdk_root = ""
compiler_config_dir = ""

def rp(path):
    return os.path.realpath(path)

def ensure_dir(path):
    return pathlib.Path(path).mkdir(parents=True, exist_ok=True)

def remove_line_containing(lef_lines, regex):
    for lef_line in lef_lines:
        match = re.search(regex, lef_line)
        if match:
            lef_lines.remove(lef_line)
    return lef_lines

def remove_version(lef_lines):
    return remove_line_containing(lef_lines, r"(.*)VERSION(.*)")

def remove_nowireextensionatpin(lef_lines):
    return remove_line_containing(lef_lines, r"(.*)NOWIREEXTENSIONATPIN(.*)")

def remove_dividerchar(lef_lines):
    return remove_line_containing(lef_lines, r"(.*)DIVIDERCHAR(.*)")

def remove_busbitchars(lef_lines):
    return remove_line_containing(lef_lines, r"(.*)BUSBITCHARS(.*)")

def remove_endlibrary(lef_lines):
    return remove_line_containing(lef_lines, r"(.*)END( *)LIBRARY(.*)")

def pre_process_merged_lef(lef_lines):
    pre_processing_steps = [remove_version, remove_nowireextensionatpin,
                            remove_dividerchar, remove_busbitchars,
                            remove_endlibrary]
    for apre_processing_step in pre_processing_steps:
        lef_lines = apre_processing_step(lef_lines)

    return lef_lines

def merge_lefs_into(build_folder, merged_filename="sky130_fd_sc_hd.merged.lef"):
    build_folder = os.path.abspath(os.path.realpath(build_folder))
    # Common header we only need one of
    header = ["VERSION 5.7 ;\n",
            "NOWIREEXTENSIONATPIN ON ;\n",
            "DIVIDERCHAR \"/\" ;\n",
            "BUSBITCHARS \"[]\" ;\n"]
    # Common footer we only need one of
    footer = ["END LIBRARY\n"]
    merged_lef_lines = []
    merged_lef_lines += header
    # tlef
    with open(os.path.abspath(os.path.join(pdk_tlef_dir, 'sky130_fd_sc_hd.tlef')), 'r') as tlef:
        merged_lef_lines += tlef.readlines()

    # lef

    # for filename in os.listdir(pdk_lef_dir):
    #     with open(os.path.abspath(os.path.join(pdk_lef_dir, filename)), 'r') as current_lef:
    #         merged_lef_lines += current_lef.readlines()

    with open(os.path.abspath(os.path.join(pdk_lef_dir, 'sky130_fd_sc_hd.lef')), 'r') as lef:
        merged_lef_lines += lef.readlines()

    merged_lef_lines = pre_process_merged_lef(merged_lef_lines)

    # remove all footers and add just one at the end
    merged_lef_lines = header + merged_lef_lines + footer
    with open(os.path.join(build_folder, merged_filename), 'w') as merged_lef:
        merged_lef.write(''.join(merged_lef_lines))

def prep(build_folder, local_pdk_root):
    global pdk_root, pdk_tech_dir, pdk_ref_dir, pdk_liberty_dir
    global pdk_lef_dir, pdk_tlef_dir
    global pdk_klayout_dir, compiler_config_dir, pdk_magic_dir
    pdk_root = os.path.abspath(os.path.realpath(local_pdk_root))
    pdk_tech_dir = os.path.join(pdk_root, 'sky130A/libs.tech')
    pdk_ref_dir = os.path.join(pdk_root, 'sky130A/libs.ref')
    pdk_liberty_dir = os.path.join(pdk_ref_dir, 'sky130_fd_sc_hd/lib')
    pdk_lef_dir = os.path.join(pdk_ref_dir, 'sky130_fd_sc_hd/lef')
    pdk_tlef_dir = os.path.join(pdk_ref_dir, 'sky130_fd_sc_hd/techlef')
    pdk_klayout_dir = os.path.join(pdk_tech_dir, 'klayout')
    pdk_magic_dir = os.path.join(pdk_tech_dir, 'magic')
    compiler_config_dir = os.path.abspath(os.path.realpath('./config'))
    merge_lefs_into(build_folder)

def run_docker(image, args):
    subprocess.run([
        "docker", "run",
        "-v",
        "%s:%s" % (pdk_root, pdk_root),
        "-v",
        "%s:%s" % (compiler_config_dir, compiler_config_dir),
        "-v",
        "%s:/mnt/dffram" % rp(".."),
        "-w", "/mnt/dffram/Compiler",
    ] + [image] + args, check=True)

def openlane(*args_tuple):
    args = list(args_tuple)
    run_docker("efabless/openlane:v0.15", args)

def sta(build_folder, design, netlist, spef_file=None):
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
            set ::env(LIB_FASTEST) {pdk_ref_dir}/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ff_n40C_1v95.lib
            set ::env(LIB_SLOWEST) {pdk_ref_dir}/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ss_100C_1v60.lib
            set ::env(CURRENT_NETLIST) {netlist}
            set ::env(DESIGN_NAME) {design}
            set ::env(BASE_SDC_FILE) /openLANE_flow/scripts/base.sdc
            source "/openLANE_flow/scripts/sta.tcl"

        """.format(
            build_folder=build_folder,
            pdk_ref_dir=pdk_ref_dir,
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
def synthesis(build_folder, design, widths_supported, word_width_bytes, out_file):
    print("--- Synthesis ---")
    chparam = ""
    if len(widths_supported) > 1:
        chparam = "catch { chparam -set WSIZE %i %s }" % (word_width_bytes, design)
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
        export LIBERTY={pdk_ref_dir}/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
        yosys {build_folder}/synth.tcl
        """.format(build_folder=build_folder, pdk_ref_dir=pdk_ref_dir))

    openlane("bash", "%s/synth.sh" % build_folder)

def floorplan(build_folder, design, wmargin_sites, hmargin_sites, width, height, in_file, out_file):
    SITE_WIDTH=0.46
    SITE_HEIGHT=2.72
    print("--- Floorplan ---")

    wmargin = wmargin_sites * SITE_WIDTH
    hmargin = hmargin_sites * SITE_HEIGHT

    full_width = width + (wmargin * 2)
    full_height = height + (hmargin * 2)

    with open("%s/fp_init.tcl" % build_folder, 'w') as f:
        f.write("""
        read_liberty {pdk_liberty_dir}/sky130_fd_sc_hd__tt_025C_1v80.lib
        read_lef {build_folder}/sky130_fd_sc_hd.merged.lef
        read_verilog {in_file}
        link_design {design}
        initialize_floorplan\\
            -die_area "0 0 {full_width} {full_height}"\\
            -core_area "{wmargin} {hmargin} {wpm} {hpm}"\\
            -site unithd\\
            -tracks {pdk_tech_dir}/openlane/sky130_fd_sc_hd/tracks.info
        write_def {out_file}
        """.format(
            build_folder=build_folder,
            pdk_tech_dir=pdk_tech_dir,
            pdk_liberty_dir=pdk_liberty_dir,
            design=design,
            wmargin=wmargin,
            hmargin=hmargin,
            wpm=width + wmargin,
            full_width=full_width,
            hpm=height + hmargin,
            full_height=full_height,
            in_file=in_file,
            out_file=out_file
        ))

    openlane("openroad", "%s/fp_init.tcl" % build_folder)


def placeram(in_file, out_file, size, building_blocks, dimensions=os.devnull, represent=os.devnull):
    print("--- placeRAM Script ---")
    unaltered = out_file + ".ref"

    run_docker("cloudv/dffram-env", [
        "python3", "-m", "placeram",
        "--output", unaltered,
        "--lef", "%s/sky130_fd_sc_hd.lef" % pdk_lef_dir,
        "--tech-lef", "%s/sky130_fd_sc_hd.tlef" % pdk_tlef_dir,
        "--size", size,
        "--write-dimensions", dimensions,
        "--represent", represent,
        "--building-blocks", building_blocks,
        in_file
    ])

    unaltered_str = open(unaltered).read()

    altered_str = re.sub(r"\+ PORT", "", unaltered_str)

    with open(out_file, 'w') as f:
        f.write(altered_str)

pin_order_file = "./pin_order.cfg"
def place_pins(build_folder, in_file, out_file):
    print("--- Pin Placement ---")
    openlane(
        "python3",
        "/openLANE_flow/scripts/io_place.py",
        "--input-lef", "%s/sky130_fd_sc_hd.merged.lef" % build_folder,
        "--input-def", in_file,
        "--config", pin_order_file,
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
        read_liberty {pdk_liberty_dir}/sky130_fd_sc_hd__tt_025C_1v80.lib
        read_lef {build_folder}/sky130_fd_sc_hd.merged.lef
        read_def {in_file}
        if [check_placement -verbose] {{
            puts "Placement failed: Check placement returned a nonzero value."
            exit 65
        }}
        puts "Placement successful."
        """.format(build_folder=build_folder,
            pdk_liberty_dir=pdk_liberty_dir,
            in_file=in_file)


    )

    openlane("openroad", "%s/verify.tcl" % build_folder)

last_image = None
def create_image(build_folder, in_file, width=256,height=256):
    global last_image
    if not os.getenv("CREATE_IMAGE") is not None:
        print("--- Create Image ---")
        openlane(
            "bash",
            "xvfb-run", "-a", "klayout", "-z",
            "-rd", "input_layout=%s" % in_file,
            "-rd", "extra_lefs=%s" % "%s/sky130_fd_sc_hd.merged.lef" % build_folder,
            "-rd", "tech_file=%s" % "%s/sky130A.lyt" % pdk_klayout_dir,
            "-rd", "width=%s" % (width),
            "-rd", "height=%s" % (height),
            "-rm", "./scripts/klayout/scrot_layout.py"
        )
        last_image = in_file + ".png"

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

        read_lef {build_folder}/sky130_fd_sc_hd.merged.lef

        read_def {in_file}

        pdngen {cfg_file} -verbose

        write_def {out_file}
        """.format(build_folder=build_folder,
                in_file=in_file,
                cfg_file=pdn_cfg_file,
                out_file=out_file)

    with open("%s/pdn.tcl" % build_folder, 'w') as f:
        f.write(pdn_tcl)
    openlane("openroad", "%s/pdn.tcl" % build_folder)

def obs_route(build_folder, metal_layer, width, height, in_file, out_file):
    print("--- Routing Obstruction Creation---")
    openlane(
        "python3",
        "/openLANE_flow/scripts/add_def_obstructions.py",
        "--lef", "%s/sky130_fd_sc_hd.merged.lef" % build_folder,
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
        lef:{build_folder}/sky130_fd_sc_hd.merged.lef
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
        source {compiler_config_dir}/openroad/sky130hd.vars
        read_liberty {pdk_liberty_dir}/sky130_fd_sc_hd__tt_025C_1v80.lib
        read_lef {build_folder}/sky130_fd_sc_hd.merged.lef
        read_def {in_file}
        global_route \\
            -guide_file {global_route_guide} \\
            -layers $global_routing_layers \\
            -clock_layers $global_routing_clock_layers \\
            -unidirectional_routing \\
            -overflow_iterations 100
        tr::detailed_route_cmd {build_folder}/tr.param
        """.format(build_folder,
            compiler_config_dir=compiler_config_dir,
            pdk_liberty_dir=pdk_liberty_dir,
            in_file=in_file,
            global_route_guide=global_route_guide,
            build_folder=build_folder))

    openlane("openroad", "%s/route.tcl" % build_folder)

def spef_extract(build_folder, def_file, spef_file=None):
    print("--- Extract SPEF ---")
    openlane("python3", "/openLANE_flow/scripts/spef_extractor/main.py",
            "--def_file", def_file,
            "--lef_file", "%s/sky130_fd_sc_hd.merged.lef"%build_folder,
            "--wire_model", "L",
            "--edge_cap_factor", "1")

def add_pwr_gnd_pins(build_folder, original_netlist,
        def_file, intermediate_file, out_file1,
        out_file2):
    print("--- Adding power and ground pins to netlist ---")

    openlane("python3", "/openLANE_flow/scripts/write_powered_def.py",
            "-d", def_file,
            "-l", "%s/sky130_fd_sc_hd.merged.lef"%build_folder,
            "--power-port", "VPWR",
            "--ground-port", "VGND",
            "-o", intermediate_file)

    with open("%s/write_pwr_gnd_verilog.tcl" % build_folder, "w") as f:
        f.write("""
        read_lef {build_folder}/sky130_fd_sc_hd.merged.lef
        read_def {def_file}
        read_verilog {netlist}
        puts "Writing the modified nl.v "
        puts "writing file"
        puts {out_file}
        write_verilog -include_pwr_gnd {out_file}
        """.format(build_folder=build_folder,netlist=original_netlist, def_file=intermediate_file,
            out_file=out_file1))

    openlane("openroad",
            "%s/write_pwr_gnd_verilog.tcl" % build_folder)

    with open("%s/rewrite_netlist.tcl" % build_folder, 'w') as f:
        f.write("""
        yosys -import
        read_verilog {verilog_file}; # usually from openroad
        write_verilog -noattr -noexpr -nohex -nodec {out_file};
        """.format(verilog_file=out_file1, out_file=out_file2))

    openlane("yosys", "-c", "%s/rewrite_netlist.tcl" % build_folder)


def write_ram_lef(build_folder, design, in_file, out_file):
    print("--- Write LEF view of the RAM Module ---")
    with open("%s/write_lef.tcl" % build_folder, "w") as f:
        f.write("""
        puts "Running magic script…"
        lef read {build_folder}/sky130_fd_sc_hd.merged.lef
        def read {in_file}
        load {design} -dereference
        lef write {out_file}
        """.format(
            build_folder=build_folder,
            design=design,
            in_file=in_file,
            out_file=out_file))

    openlane("magic",
            "-dnull",
            "-noconsole",
            "-rcfile",
            "%s/sky130A.magicrc" % pdk_magic_dir,
            "%s/write_lef.tcl" % build_folder)

def write_ram_lib(build_folder, design, netlist, libfile):
    print("--- Write LIB view of the RAM Module ---")
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
        lef read {build_folder}/sky130_fd_sc_hd.merged.lef
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
        """.format(build_folder=build_folder, design=design, in_1=in_1))

    with open("%s/lvs.sh" % build_folder, "w") as f:
        f.write("""
        magic -rcfile {pdk_magic_dir}/sky130A.magicrc -noconsole -dnull < {build_folder}/lvs.tcl
        mv *.ext *.spice {build_folder}
        netgen -batch lvs "{build_folder}/{design}.spice {design}" "{in_2} {design}" -full
        mv comp.out {report}
        """.format(build_folder=build_folder,
            pdk_magic_dir=pdk_magic_dir,
            design=design,
            in_1=in_1,
            in_2=in_2,
            report=report))

    openlane("bash", "%s/lvs.sh" % build_folder)

def antenna_check(build_folder, def_file, out_file):
    # using openroad antenna check
    print("--- Antenna Check ---")
    with open("%s/antenna_check.tcl" % build_folder, 'w') as f:
        f.write("""
            set ::env(REPORTS_DIR) {build_folder}
            set ::env(MERGED_LEF_UNPADDED) {build_folder}/sky130_fd_sc_hd.merged.lef
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
@click.option("--only", default=None, help="Only execute these comma;delimited;steps")
@click.option("--skip", default=None, help="Skip these comma;delimited;steps")
@click.option("-p", "--pdk_root", required=True, help="path to sky130A pdk")
@click.option("-s", "--size", required=True, help="Size")
@click.option("-b", "--building-blocks", default="sky130A:ram/legacy", help="Format <pdk>:<name>: Name of the building blocks to use.")
@click.option("-v", "--variant", default=None, help="Use design variants (such as 1RW1R)")
def flow(frm, to, only, pdk_root, skip, size, building_blocks, variant):
    global bb_used, pin_order_file

    if variant == "DEFAULT":
        variant = None

    pdk, blocks = building_blocks.split(":")

    bb_dir = os.path.join(".", pdk, "BB", blocks)
    if not os.path.isdir(bb_dir):
        print("Looking for building blocks in :", bb_dir)
        print("Building blocks %s not found." % building_blocks)
        exit(66)

    bb_used = os.path.join(bb_dir, "model.v")
    config_file = os.path.join(bb_dir, "config.yml")
    config = yaml.safe_load(open(config_file))

    optional_pin_order_file = os.path.join(bb_dir, "pin_order.cfg")
    if os.path.exists(optional_pin_order_file):
        pin_order_file = optional_pin_order_file

    m = re.match(r"(\d+)x(\d+)", size)
    if m is None:
        print("Invalid RAM size '%s'." % size)
        exit(64)

    words = int(m[1])
    word_width = int(m[2])
    word_width_bytes = word_width / 8

    if os.getenv("FORCE_ACCEPT_SIZE") is None:
        if words not in config["counts"] or word_width not in config["widths"]:
            print("Size %s not supported by %s." % (size, building_blocks))
            exit(64)

        if variant not in config["variants"]:
            print("Variant %s is unsupported by %s." % (variant, building_blocks))
            exit(64)

    wmargin, hmargin = (16, 2) # in sites # note that the minimum site width is tiiiinnnyyy
    variant_string = (("_%s" % variant) if variant is not None else "")
    design_name_template = config["design_name_template"]
    design = os.getenv("FORCE_DESIGN_NAME") or design_name_template.format(**{
        "count": words,
        "width": word_width,
        "width_bytes": word_width_bytes,
        "variant": variant_string
    })
    build_folder = "./build/%s_SIZE%i" % (design, word_width)

    ensure_dir(build_folder)

    def i(ext=""):
        return "%s/%s%s" %(build_folder, design, ext)

    prep(build_folder, pdk_root)

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
    except Exception:
        width, height = 20000, 20000


    def placement(in_width, in_height):
        nonlocal width, height
        floorplan(build_folder, design, wmargin, hmargin, in_width, in_height, netlist, initial_floorplan)
        placeram(initial_floorplan, initial_placement, size, building_blocks, dimensions_file)
        width, height = map(lambda x: float(x), open(dimensions_file).read().split("x"))
        floorplan(build_folder, design, wmargin, hmargin, width, height, netlist, final_floorplan)
        placeram(final_floorplan, no_pins_placement, size, building_blocks)
        place_pins(build_folder, no_pins_placement, final_placement)
        verify_placement(build_folder, final_placement)
        create_image(build_folder, final_placement, width, height)

    steps = [
        (
            "synthesis",
            lambda: synthesis(
                build_folder,
                design,
                config["widths"],
                word_width_bytes,
                netlist
            )
        ),
        ("sta_1", lambda: sta(build_folder, design, netlist)),
        ("placement", lambda: placement(width, height)),
        (
            "pdngen",
            lambda: pdngen(build_folder, width, height, final_placement, pdn)
        ),
        (
            "obs_route",
            lambda: obs_route(build_folder, 5, width, height, pdn, obstructed)
        ),
        (
            "routing",
            lambda: (
                route(build_folder, obstructed, routed),
                create_image(build_folder, routed)
            )
        ),
        (
            "sta_2",
            lambda: (
                spef_extract(build_folder, routed, spef),
                sta(build_folder, design, netlist, spef)
            )
        ),
        (
            "add_pwr_gnd_pins",
            lambda: (
                add_pwr_gnd_pins(
                    build_folder,
                    netlist,
                    routed,
                    powered_def,
                    norewrite_powered_netlist,
                    powered_netlist
                ),
                create_image(build_folder, powered_def)
            )
        ),
        (
            "write_lef",
            lambda: write_ram_lef(
                build_folder,
                design,
                routed,
                lef_view
            )
        ),
        (
            "write_lib",
            lambda: write_ram_lib(
                build_folder,
                design,
                powered_netlist,
                lib_view
            )
        ),
        (
            "antenna_check",
            lambda: antenna_check(
                build_folder,
                routed,
                antenna_report
            )
        ),
        (
            "lvs",
            lambda: lvs(
                build_folder,
                design,
                routed,
                powered_netlist,
                report
            )
        )
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
                action()
        if to == name:
            execute_steps = False

    elapsed = time.time() - start

    print("Done in %.2fs." % elapsed)

    if last_image is not None and sys.platform == "darwin":
        subprocess.run([
            "open",
            last_image
        ], check=True)

def main():
    try:
        flow()
    except Exception:
        print("An unhandled exception has occurred.", traceback.format_exc())
        exit(69)

if __name__ == '__main__':
    main()
