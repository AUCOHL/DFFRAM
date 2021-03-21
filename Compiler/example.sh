if [ ! -d ./example_support ]; then
     echo "Untarring support files…"
     tar -xJf ./example_support.tar.xz
fi

export DESIGN=SRAM8x32

# 1. Synthesis
(cd ../Handcrafted/Models; DESIGN=SRAM8x32 yosys ../Synth/syn.tcl)

# 2. Floorplan Initialization
cat <<HEREDOC > ./example_support/openroad_fp_script.tcl
read_liberty ./example_support/sky130_fd_sc_hd__tt_025C_1v80.lib

read_lef ./example_support/sky130_fd_sc_hd.merged.lef

read_verilog ../Handcrafted/Models/$DESIGN.gl.v

link_design $DESIGN

initialize_floorplan -die_area "0 0 2000 2000" -core_area "100 100 1900 1900" -site unithd -tracks ./example_support/tracks_hd.info

remove_buffers

auto_place_pins met1

report_checks -fields {input slew capacitance} -format full_clock

write_def ./$DESIGN.def
HEREDOC

docker run\
     -v $PDK_ROOT:$PDK_ROOT\
     -v $(realpath ..):/mnt/dffram\
     -w /mnt/dffram/Compiler\
     efabless/openlane\
     openroad ./example_support/openroad_fp_script.tcl

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
cat <<HEREDOC > ./example_support/openroad_vp_script.tcl
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
     openroad ./example_support/openroad_vp_script.tcl