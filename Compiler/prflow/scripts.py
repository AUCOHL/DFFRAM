from .config import *

from pathlib import Path

helpString = """
This is an example flow for use with placeRAM.

There is a support tarball included for this file that is checked into the
repository.

It goes all the way from elaborating the custom Verilog netlists to LVS.

This script requires docker and will pull openlane and other dependencies.
If you would not like to use either, feel free to substitute any of the
invocations with local ones.
"""

synthTclScript = """
yosys -import

set SCL $env(LIBERTY)
set DESIGN $env(DESIGN)

read_liberty -lib -ignore_miss_dir -setattr blackbox $SCL
read_verilog BB.v

hierarchy -check -top $DESIGN

synth -top $DESIGN -flatten

splitnets
opt_clean -purge

write_verilog -noattr -noexpr -nodec {}/$DESIGN.gl.v
stat -top $DESIGN -liberty $SCL

exit
""".format(BUILD_FOLDER)

synthShellScript = """
export DESIGN={}
export LIBERTY=./example_support/sky130_fd_sc_hd__tt_025C_1v80.lib
yosys {}/synth.tcl
""".format(DESIGN, BUILD_FOLDER)


floorplanTclScript = """
read_liberty ./example_support/sky130_fd_sc_hd__tt_025C_1v80.lib

read_lef ./example_support/sky130_fd_sc_hd.merged.lef

read_verilog {}/{}.gl.v

link_design {}

initialize_floorplan\
     -die_area "0 0 {} {}"\
     -core_area "{} {} {} {}"\
     -site unithd\
     -tracks ./example_support/sky130hd.tracks

ppl::set_hor_length 4
ppl::set_ver_length 4
ppl::set_hor_length_extend 2
ppl::set_ver_length_extend 2
ppl::set_ver_thick_multiplier 4
ppl::set_hor_thick_multiplier 4

place_pins\
    -random\
    -random_seed 42\
    -min_distance 5\
    -hor_layers 4\
    -ver_layers 3\

report_checks -fields {{input slew capacitance}} -format full_clock

write_def {}/{}.def
"""
floorplanTclScriptFilled = floorplanTclScript.format(
        BUILD_FOLDER,
        DESIGN,
        DESIGN,
        FULL_WIDTH, FULL_HEIGHT,
        MARGIN, MARGIN, DESIGN_WIDTH, DESIGN_HEIGHT,
        BUILD_FOLDER, DESIGN)

placeDockerCmd = """
docker run --rm\
     -v {}:/mnt/dffram\
     -w /mnt/dffram/Compiler\
     cloudv/dffram-env\
     python3 -m placeram\
     --represent {}/{}.txt\
     --output {}/{}.placed.def\
     --lef ./example_support/sky130_fd_sc_hd.lef\
     --tech-lef ./example_support/sky130_fd_sc_hd.tlef\
     --size {}\
     {}/{}.def
""".format(PROJECT_ROOT,
        BUILD_FOLDER, DESIGN,
        BUILD_FOLDER, DESIGN,
        SIZE,
        BUILD_FOLDER, DESIGN,)

removePortsCmd = "rm -f {}/{}.placed.def.ref".format(BUILD_FOLDER, DESIGN)

backupPlacedDesignCmd = "mv {}/{}.placed.def {}/{}.placed.def.ref".format(BUILD_FOLDER,
        DESIGN,
        BUILD_FOLDER,
        DESIGN)

removeUnnecessaryPortsCmd = """
sed "'s/+ PORT//g'" {}/{}.placed.def.ref > {}/{}.placed.def
""".format(BUILD_FOLDER, DESIGN, BUILD_FOLDER, DESIGN)

verifyTclScript = """
read_liberty ./example_support/sky130_fd_sc_hd__tt_025C_1v80.lib

read_lef ./example_support/sky130_fd_sc_hd.merged.lef

read_def {}/{}.placed.def

if [check_placement -verbose] {{
    puts \"Placement failed: Check placement returned a nonzero value.\"
    exit 65
}}

puts \"Placement successful.\"
""".format(BUILD_FOLDER, DESIGN)

routeTclScript = """
source ./example_support/sky130hd.vars

read_liberty ./example_support/sky130_fd_sc_hd__tt_025C_1v80.lib

read_lef ./example_support/sky130_fd_sc_hd.merged.lef

read_def {}/{}.placed.def

global_route \
     -guide_file {}/route.guide\
     -layers $global_routing_layers\
     -clock_layers $global_routing_clock_layers\
     -unidirectional_routing\
     -overflow_iterations 100\

tr::detailed_route_cmd {}/tr.param
""".format(BUILD_FOLDER, DESIGN, BUILD_FOLDER, BUILD_FOLDER)

trParams = """
lef:./example_support/sky130_fd_sc_hd.merged.lef
def:{}/{}.placed.def
guide:{}/route.guide
output:{}/{}.routed.def
outputguide:{}/{}.guide
outputDRC:{}/{}.drc
threads:8
verbose:1
""".format(BUILD_FOLDER, DESIGN,
        BUILD_FOLDER,
        BUILD_FOLDER, DESIGN,
        BUILD_FOLDER, DESIGN,
        BUILD_FOLDER, DESIGN)


lvsTclScript = """
puts "Running magic script…"
lef read ./example_support/sky130_fd_sc_hd.merged.lef
def read {}/{}.routed.def
load {} -dereference
extract do local
extract no capacitance
extract no coupling
extract no resistance
extract no adjust
extract unique
extract

ext2spice lvs
ext2spice
""".format(BUILD_FOLDER, DESIGN, DESIGN)


lvsShellScript = """
magic -rcfile ./example_support/sky130A.magicrc -noconsole -dnull < {}/lvs.tcl
mv *.ext *.spice {}
netgen -batch lvs "{}/{}.spice {}" "{}/{}.gl.v {}" -full
mv comp.out {}/lvs.rpt
""".format(BUILD_FOLDER,
        BUILD_FOLDER,
        BUILD_FOLDER, DESIGN, DESIGN,
        BUILD_FOLDER,
        DESIGN,DESIGN,
        BUILD_FOLDER)

