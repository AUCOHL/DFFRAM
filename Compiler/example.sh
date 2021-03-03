if [ ! -d ./example_support ]; then
     echo "Untarring support files…"
     tar -xJf ./example_support.tar.xz
fi

# # 1. Synthesis
# (cd ../Handcrafted/Models; yosys ../Synth/syn.tcl)

# # 2. Floorplan Initialization
# cat <<HEREDOC > ./example_support/openroad_script.tcl
# read_liberty ./example_support/sky130_fd_sc_hd__tt_025C_1v80.lib

# read_lef ./example_support/sky130_fd_sc_hd.merged.lef

# read_verilog ../Handcrafted/Models/DFFRAM.gl.v

# link_design DFFRAM

# initialize_floorplan -die_area "0 0 2000 2000" -core_area "100 100 1900 1900" -site unithd -tracks ./example_support/tracks_hd.info

# remove_buffers

# auto_place_pins met1

# report_checks -fields {input slew capacitance} -format full_clock

# write_def ./DFFRAM.def
# HEREDOC

# docker run\
#      -v $PDK_ROOT:$PDK_ROOT\
#      -v $(realpath ..):/mnt/dffram\
#      -w /mnt/dffram/Compiler\
#      efabless/openlane\
#      openroad ./example_support/openroad_script.tcl

## Interactive 
# docker run -ti\
#      -v $PDK_ROOT:$PDK_ROOT\
#      -v $(realpath ..):/mnt/dffram\
#      -w /mnt/dffram/Compiler\
#      efabless/openlane\
#      openroad

# 3. PlaceRAM

## Old
# python3 placeRAM.py\
#      --def ./DFFRAM.def\
#      --lef $PDK_ROOT/sky130/sky130A/libs.ref/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef\
#      --tech-lef $PDK_ROOT/sky130/sky130A/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd.tlef\
#      --output-def ./placed.def
## New
python3 placeRAM.py\
     --output ./DFFRAM.placed.def\
     --lef ./example_support/sky130_fd_sc_hd.lef\
     --tech-lef ./example_support/sky130_fd_sc_hd.tlef\
     ./DFFRAM.def