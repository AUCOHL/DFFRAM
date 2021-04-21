#!/usr/bin/env python3
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

# Not true synthesis, just elaboration.
def synthesis(build_folder, design, out_file):
    print("--- Synthesis ---")
    with open("%s/synth.tcl" % build_folder, 'w') as f:
        f.write("""
        yosys -import
        set vtop {design}
        set SCL $env(LIBERTY)
        read_liberty -lib -ignore_miss_dir -setattr blackbox $SCL
        read_verilog BB.v
        hierarchy -check -top {design}
        synth -top {design} -flatten
        opt_clean -purge
        splitnets
        opt_clean -purge
        write_verilog -noattr -noexpr -nodec {out_file}
        stat -top {design} -liberty $SCL
        exit
        """.format(design=design, out_file=out_file))

    with open("%s/synth.sh" % build_folder, 'w') as f:
        f.write("""
        export LIBERTY=./example_support/sky130_fd_sc_hd__tt_025C_1v80.lib
        yosys %s/synth.tcl
        """ % build_folder)

    openlane("bash", "%s/synth.sh" % build_folder)

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


def placeram(in_file, out_file, size, dimensions=os.devnull, represent=os.devnull):
    print("--- placeRAM Script ---")
    unaltered = out_file + ".ref"

    run_docker("cloudv/dffram-env", [
        "python3", "-m", "placeram",
        "--output", unaltered,
        "--lef", "./example_support/sky130_fd_sc_hd.lef",
        "--tech-lef", "./example_support/sky130_fd_sc_hd.tlef",
        "--size", size,
        "--write-dimensions", dimensions,
        "--represent", represent,
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
    # using the tcl interface to openlane, openroad seems
    # a bit dangerous to use with regards to obstruction
    # creation
    openlane(
        "python3",
        "/openLANE_flow/scripts/add_def_obstructions.py",
        "--lef", "./example_support/sky130_fd_sc_hd.merged.lef",
        "--input-def", in_file,
        "--obstructions",
        "met{metal_layer} 0 0 {width} {height}".format(metal_layer=metal_layer,
            width=width,
            height=height),
        "--output", out_file
    )

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

# ("add_pwr_gnd_pins", lambda: add_pwr_gnd_pins(build_folder, pdn,
# powered_def,
# norewrite_powered_netlist,
# powered_netlist)),
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

@click.command()
@click.option("-f", "--frm", default="synthesis", help="Start from this step")
@click.option("-t", "--to", default="lvs", help="End after this step")
@click.option("--only", default=None, help="Only execute this step")
@click.option("-s", "--size", required=True, help="Size")
@click.option("-d", "--disable_routing", is_flag=True, default=False, help="disable routing")
def flow(frm, to, only, size, disable_routing=False):
    design = "RAM%s" % size
    build_folder = "./build/%s" % design

    ensure_dir(build_folder)

    def i(ext):
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
    lef_view = i(".lef")
    powered_def = i(".powered.def")
    norewrite_powered_netlist = i(".norewrite_powered.nl.v")
    powered_netlist = i(".powered.nl.v")
    report = i(".rpt")

    try:
        width, height = map(lambda x: float(x), open(dimensions_file).read().split("x"))
        height += 3
    except Exception:
        width, height = 20000, 20000


    def placement(in_width, in_height):
        nonlocal width, height
        floorplan(build_folder, design, 5, in_width, in_height, netlist, initial_floorplan)
        placeram(initial_floorplan, initial_placement, size, dimensions_file)
        width, height = map(lambda x: float(x), open(dimensions_file).read().split("x"))
        height += 3 # OR fails to create the proper amount of rows without some slack.
        floorplan(build_folder, design, 5, width, height, netlist, final_floorplan)
        placeram(final_floorplan, no_pins_placement, size)
        place_pins(no_pins_placement, final_placement)
        verify_placement(build_folder, final_placement)

    steps = [
        ("synthesis", lambda: synthesis(build_folder, design, netlist)),
        ("placement", lambda: placement(width, height)),
        ("pdngen", lambda: pdngen(build_folder, width, height, final_placement, pdn)),
        ("obs_route", lambda: obs_route(build_folder, 5, width, height, pdn,
            obstructed)),
        ("routing", lambda: route(build_folder, obstructed, routed)),
        ("add_pwr_gnd_pins", lambda: add_pwr_gnd_pins(build_folder, netlist,
            routed,
            powered_def,
            norewrite_powered_netlist,
            powered_netlist)),
        ("write_lef", lambda: write_RAM_LEF(build_folder, design, routed,
            lef_view)),
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
