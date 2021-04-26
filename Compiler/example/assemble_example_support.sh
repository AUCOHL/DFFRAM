#!/bin/bash
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

set -x
rm -rf ./example_support
mkdir -p ./example_support/

c() {
    cp $1 ./example_support
}

if [ ! -d $PDK_ROOT/sky130A ]; then
    echo "$PDK_ROOT/sky130A is not a directory. You cannot assemble example the example support tarball on this computer." > /dev/stderr
    exit 66
fi

cp -r $PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/mag ./example_support/magic_reference_cells
c $PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib 
c $PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd.tlef 
c $PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef 
c $PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/sky130_fd_sc_hd.merged.lef # Requires handmerge
c $PDK_ROOT/sky130A/libs.tech/magic/sky130A.tech
c $PDK_ROOT/sky130A/libs.tech/magic/sky130A.tcl

cat <<HEREDOC > ./example_support/sky130A.magicrc
puts stdout "Sourcing design .magicrc for technology sky130A ..."

# Put grid on 0.005 pitch.  This is important, as some commands don't
# rescale the grid automatically (such as lef read?).

set scalefac [tech lambda]
if {[lindex $scalefac 1] < 2} {
    scalegrid 1 2
}

# drc off
drc euclidean on
# Change this to a fixed number for repeatable behavior with GDS writes
# e.g., "random seed 12345"
catch {random seed}

# loading technology
tech load ./example_support/sky130A.tech

# load device generator
source ./example_support/sky130A.tcl

# set units to lambda grid 
snap lambda

# set sky130 standard power, ground, and substrate names
set VDD VPWR
set GND VGND
set SUB VSUBS

addpath ./exmaple_support/magic_reference_cells

# add path to GDS cells

# add path to IP from catalog.  This procedure defined in the PDK script.
catch {magic::query_mylib_ip}
# add path to local IP from user design space.  Defined in the PDK script.
catch {magic::query_my_projects}
HEREDOC

curl -L https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD/5f67d3983393bcf1eb7e873b4b894484c7818fae/test/sky130hd/sky130hd.tracks > ./example_support/sky130hd.tracks
curl -L https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD/5f67d3983393bcf1eb7e873b4b894484c7818fae/test/sky130hd/sky130hd.vars > ./example_support/sky130hd.vars

rm -f ./example_support.tar.xz
tar -cJvf example_support.tar.xz ./example_support