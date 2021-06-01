# Basic
```sh
git clone https://github.com/Cloud-V/DFFRAM 
cd DFFRAM/Compiler
python3 -m pip install -r requirements.txt
./prflow.py -s 8x32 # you can choose from those sizes: 32x32, 128x32, 512x32, 1024x32, 2048x32  
```

# Advanced
The compilation flow at a minimum needs two options: the building blocks and the size.

```sh
./prflow.py -b sky130A:ram/legacy -s8x32
```

The building block set `platform:name` corresponds to ./Compiler/\<platform\>/BB/\<name\>/model.v. Building block sets are fundamentally similar with a number of exceptions, most importantly, the SCL used and supported sizes.

The bleeding edge building block set is `sky130A:ram`, but the default is `ram/legacy`. Legacy only supports x32 sizes.

## Options
For a full list of options, please invoke:
```
./prflow.py --help
```

### Secret Menu
Prflow supports a number of secret options you can use to further customize your experience. They are all passed as environment variables:

Variable Name|Effect
-|-
PRFLOW_CREATE_IMAGE|If set to any value, a step after placement and routing that creates an image with Klayout is added. It's good for sanity checks.
FORCE_ACCEPT_SIZE|Prflow checks that you are not using a size not officially marked supported as available by a certain building block set. If this environment variable is set to any value, the check is bypassed.
FORCE_DESIGN_NAME|Design names are found based on the size. If you'd like to force prflow to use a specific design name instead, set this environment variable to that name.


## Overview of the steps of the flow
1. synthesis : Obtain gate level netlist from the verilog top level module

2. placement : perform custom placement of the RAM module usine placeRAM.py
    * This is the most complex step. Floorplanning and placement occurs **once to get the size** and **once again** with the size from the previous run used an input. This is to avoid using heuristics: placement is really fast. There's really no need.

3. pdngen : Generate power distribution network

4. obs_route : Create obstruction/blockage for the routing algorithm on metal layer 5.

5. routing : Route the design

6. add_pwr_gnd_pins : Add power and ground pins to the verilog gate level netlist obtained from synthesis, needed for lvs

7. write_lef : Write a lef view of the design

8. write_lib : Write a lib view of the design

9. antenna_check : Check for antenna rules violations after routing 

10. lvs : Perform Layout vs. Schematic check after routing using Magic.
