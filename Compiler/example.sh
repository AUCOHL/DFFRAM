if [ ! -d ./example_support ]; then
     echo "Untarring support files…"
     tar -xJf ./example_support.tar.xz
fi

set -e

DESIGN=SRAM8x32

mkdir -p ./build/

BUILD_FOLDER=./build/$DESIGN
mkdir -p $BUILD_FOLDER

# 1. Synthesis
(cd ../Handcrafted/Models; DESIGN=SRAM8x32 yosys ../Synth/syn.tcl)

# 2. Floorplan Initialization
cat <<HEREDOC > $BUILD_FOLDER/fp_init.tcl
read_liberty ./example_support/sky130_fd_sc_hd__tt_025C_1v80.lib

read_lef ./example_support/sky130_fd_sc_hd.merged.lef

read_verilog ../Handcrafted/Models/$DESIGN.gl.v

link_design $DESIGN

initialize_floorplan\
     -die_area "0 0 500 500"\
     -core_area "0 0 500 500"\
     -site unithd\
     -tracks ./example_support/sky130hd.tracks

remove_buffers

ppl::set_hor_length 4
ppl::set_ver_length 4
ppl::set_hor_length_extend 2
ppl::set_ver_length_extend 2
ppl::set_ver_thick_multiplier 4
ppl::set_hor_thick_multiplier 4

place_pins\
     -random \
 	-random_seed 42 \
 	-min_distance 5 \
 	-hor_layers 4\
 	-ver_layers 3

report_checks -fields {input slew capacitance} -format full_clock

write_def ./$DESIGN.def
HEREDOC

docker run\
     -v $PDK_ROOT:$PDK_ROOT\
     -v $(realpath ..):/mnt/dffram\
     -w /mnt/dffram/Compiler\
     efabless/openlane\
     openroad $BUILD_FOLDER/fp_init.tcl

# # Interactive 
# docker run -ti\
#      -v $PDK_ROOT:$PDK_ROOT\
#      -v $(realpath ..):/mnt/dffram\
#      -w /mnt/dffram/Compiler\
#      efabless/openlane\
#      openroad

# 3. PlaceRAM
python3 -m placeram\
     --output ./$DESIGN.placed.def\
     --lef ./example_support/sky130_fd_sc_hd.lef\
     --tech-lef ./example_support/sky130_fd_sc_hd.tlef\
     --size 8x32\
     ./$DESIGN.def

# 4. Verify Placement
cat <<HEREDOC > $BUILD_FOLDER/verify.tcl
read_liberty ./example_support/sky130_fd_sc_hd__tt_025C_1v80.lib

read_lef ./example_support/sky130_fd_sc_hd.merged.lef

read_def ./$DESIGN.placed.def

if [check_placement -verbose] {
    puts "Placement failed: Check placement returned a nonzero value."
} else {
    puts "Placement successful!"
}
HEREDOC

docker run\
     -v $PDK_ROOT:$PDK_ROOT\
     -v $(realpath ..):/mnt/dffram\
     -w /mnt/dffram/Compiler\
     efabless/openlane\
     openroad $BUILD_FOLDER/verify.tcl

# 5. Attempt Routing
cat <<HEREDOC > $BUILD_FOLDER/route.tcl
source ./example_support/sky130hd.vars

read_liberty ./example_support/sky130_fd_sc_hd__tt_025C_1v80.lib

read_lef ./example_support/sky130_fd_sc_hd.merged.lef

read_def ./$DESIGN.placed.def

global_route \
  -guide_file $BUILD_FOLDER/route.guide \
  -layers \$global_routing_layers \
  -clock_layers \$global_routing_clock_layers \
  -unidirectional_routing \
  -overflow_iterations 100

tr::detailed_route_cmd $BUILD_FOLDER/tr.param
HEREDOC

cat <<HEREDOC > $BUILD_FOLDER/tr.param
lef:./example_support/sky130_fd_sc_hd.merged.lef
def:./$DESIGN.placed.def
guide:$BUILD_FOLDER/route.guide
output:$DESIGN.routed.def
outputguide:$BUILD_FOLDER/$DESIGN.guide
outputDRC:$BUILD_FOLDER/$DESIGN.drc
threads:8
verbose:1
HEREDOC

docker run\
     -v $PDK_ROOT:$PDK_ROOT\
     -v $(realpath ..):/mnt/dffram\
     -w /mnt/dffram/Compiler\
     efabless/openlane\
     openroad $BUILD_FOLDER/route.tcl


     # def -> gdsII (magic) and def -> lef (magic)