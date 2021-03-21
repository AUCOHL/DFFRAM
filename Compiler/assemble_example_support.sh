set -x
rm -rf ./example_support
mkdir -p ./example_support/
curl -L https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-flow-scripts/9360ae65b156beb54c8dccd1d1763df6a6fc2c2a/flow/platforms/sky130hd/tracks_hd.info > ./example_support/tracks_hd.info
curl -L https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD/master/test/sky130hd/sky130hd.vars > ./example_support/sky130hd.vars
cp $PDK_ROOT/sky130/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib ./example_support
cp $PDK_ROOT/sky130/sky130A/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd.tlef ./example_support
cp $PDK_ROOT/sky130/sky130A/libs.ref/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef ./example_support
cp $PDK_ROOT/sky130/sky130A/libs.ref/sky130_fd_sc_hd/sky130_fd_sc_hd.merged.lef ./example_support # You'll need to handmerge that one
rm -f ./example_support.tar.xz
tar -cJf example_support.tar.xz ./example_support