# DFFRAM Compiler
![CI Badge](https://github.com/Cloud-V/DFFRAM/actions/workflows/main.yml/badge.svg?branch=main)

Standard Cell Library based Memory Compiler using DFF cells.

The objective of this project is to develop DFF-based RAM and Register File (RegF) compiler that utilizes standard cell libraries following a standard ASIC implementation approach. The compiler generates different views (HDL netlist, HDL functional models, LEF, GDS, Timing, …) for a given configuration set. 

The layout generated from the compiler will be highly compacted (we target over 95% placement density) as the cells are placed on the floor plan using a custom placer. Moreover, the custom placer ensures that the routing will be relatively simple. The project will consider the creation of a custom router if automatic routing using open-source global and detailed routers does not give good results, though, they are, so far!

## Compiler
A beta version of the compiler is under the `Compiler/` directory. Check [its Readme](./Compiler/Readme.md) for more info. Currently, it can generate the following configurations:
- 128x32 (512 bytes) single port RAM with byte write enable.
- 512x32 (2kbytes) single port RAM with byte write enable.
- 2048x32 (8kbytes) single port RAM with byte write enable.

Below is the Compiler-placed and routed [RAM2048x32 (8 kbytes) module](./Compiler/BB.v) ![Layout](./Compiler/docs/img/8kb_layout.png) 

<table>
  <tr>
    <th rowspan="2">Size*</th> 
    <th colspan="2">OpenRAM**</th> 
    <th colspan="2">DFFRAM Compiler</th> 
    <th colspan="2">DFFRAM/OpenLane</th> 
    <th colspan="2">RTL/OpenLane</th>
  </tr>
  <tr style="border-top:4px solid darkblue;">
    <td> Dim (microns) </td> <td> Bit Density (bits/mm^2) </td>
    <td> Dim (microns) </td> <td> Bit Density (bits/mm^2) </td>
    <td> Dim (microns) </td> <td> Bit Density (bits/mm^2) </td>
    <td> Dim (microns) </td> <td> Bit Density (bits/mm^2) </td>
  </tr>
  <tr>
    <td> 512 bytes </td>
    <td> N/A </td> <td> N/A </td>
    <td> 395.6 x 388.96 </td> <td> 26,619 </td>
    <td> TBD </td> <td> TBD </td>
    <td> 680.25 x 690.97 </td> <td> 8,714 </td>
  </tr>
  <tr>
    <td> 1 kbytes </td>
    <td> 386 x 456 </td> <td> 46,541 </td>
    <td> 788.44 x 394.4 <td> 26,344 </td>
    <td> TBD </td> <td> TBD </td>
    <td> 1,050 x 1,060 </td> <td> 7,360 </td>
  </tr>
  <tr>
    <td> 2 kbytes </td>
    <td> 659.98 x 398.18  </td> <td> 62,372 </td>
    <td> 793.5 x 783.36 </td> <td> 26,358 </td>
    <td> TBD </td> <td> TBD </td>
    <td> 1,439.615 x 1,450.335 </td> <td> 7,847 </td>
  </tr>
  <tr>
    <td> 4 kbytes </td>
    <td> 670.86 x 651.14 </td> <td> 75,014 </td>
    <td> 1,584.24 x 788.8 </td> <td> 26,196 </td>
    <td> TBD </td> <td> TBD </td>
    <td> 2,074 x 2,085 </td> <td> 7,578 </td>
    
  </tr>
  <tr>
    <td> 8 kbytes </td>
    <td> N/A </td> <td> N/A </td>
    <td> 1,589 x 1,572</td> <td> 26,229 </td>
    <td> TBD </td> <td> TBD </td>
    <td> 2,686.610 x 2,697.330 </td> <td> 9,043 </td>
  </tr>
</table>

* All support 32-bit word reads and 1, 2, and 4 bytes writes.  
* Values are based on the original layout produced by the compiler. OpenRAM macros are typically wrapped to be useful w/ automated PnR ASIC flows.

For more about the Handcrafted models, check the [Handcrafted Readme](./Handcrafted/docs/Readme.md).

# Using the Compiler (WIP)

The prflow.py script at least needs the size of the RAM module, implemented in [BB.v](./Compiler/BB.v)

Run this
```shell
git clone https://github.com/Cloud-V/DFFRAM 
cd DFFRAM/Compiler
./prflow.py -s 8x32 # you can choose from those sizes: 32x32, 128x32, 512x32, 1024x32, 2048x32  
```
### Options

```
./prflow.py    
    -f , --frm # Start from this step
    -t , --to # End after this step
    --only # Only execute this step
    -s , --size
    -d , --disable_routing

```

### Steps

1- synthesis : Obtain gate level netlist from the verilog top level module

2- placement : perform custom placement of the RAM module usine placeRAM.py

3- pdngen : Generate power distribution network

4- obs_route : Create Obstruction/Blockage for routing algorithm on metal layer 5

5- routing : Route the design

6- add_pwr_gnd_pins : Add power and ground pins to the verilog gate level netlist obtained from synthesis, needed for lvs

7- write_lef : Write a lef view of the design

8- write_lib : Write a lib view of the design

9- antenna_check : Check for antenna rules violations after routing 

10- lvs : perform Layout Vs Schematic check after routing


# ⚖️ Copyright and Licensing
Copyright ©2020-2021 The American University in Cairo and the Cloud V Project.

Licensed under the Apache License, Version 2.0 (the "Open Source License");
you may not use this file except in compliance with the Open Source License.
You may obtain a copy of the Open Source License at the root of this repository
(see the file 'License') or at

> http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the Open Source License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the Open Source License for the specific language governing permissions and
limitations under the Open Source License.
