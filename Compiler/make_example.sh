## Get magic
##  CC=gcc-10 CXX=g++-10 ./configure --with-tcl=/usr/local/opt/tcl-tk/ --with-tk=/usr/local/opt/tcl-tk/
##  make && make install
## Get skywater
##  make timing
## Get open_pdks
##  ./configure --enable-sky130-pdk=$EF_DIR/skywater-pdk --with-sky130-local-path=/usr/local/pdk/sky130 --disable-xschem
##  make && make install
## Get OpenDB (Ahmed Ghazy's Fork)
##  Build using the normal instructions
##  On Mac go to ./build/src/swig/python, rename the .dylib to .so then run setup.py

# Requires PDK_ROOT env var set

# # 1. Synthesis
# (cd ../Handcrafted/Models; yosys ../Synth/syn.tcl)

# # 2. Floorplan Initialization
# echo <<HD
# read_liberty /usr/local/pdk/sky130/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib

# read_lef /usr/local/pdk/sky130/sky130A/libs.ref/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef

# read_verilog ../Handcrafted/Models/DFFRAM.gl.v

# link_design DFFRAM

# initialize_floorplan -utilization 95 -site dffrs

# write_def ./DFFRAM.def
# HD > ./openroad_script.tcl

# docker run\
#      -v $PDK_ROOT:$PDK_ROOT\
#      -v $(realpath ..):/mnt/dffram\
#      -w /mnt/dffram/Compiler\
#      efabless/openlane\
#      openroad ./openroad_script.tcl

# 3. PlaceRAM
python3 placeRAM.py\
     --def ./DFFRAM.def\
     --lef $PDK_ROOT/sky130/sky130A/libs.ref/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef\
     --tech-lef $PDK_ROOT/sky130/sky130A/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd.tlef\
     --output-def ./placed.def