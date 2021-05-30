# DFFRAM Compiler
![CI Badge](https://github.com/Cloud-V/DFFRAM/actions/workflows/main.yml/badge.svg?branch=main)

Standard Cell Library based Memory Compiler using DFF cells.

The objective of this project is to develop a DFF/Latch-based RAM and Register File custom compilation flow that utilizes standard cell libraries following a standard ASIC implementation approach. Different views (HDL netlist, HDL functional models, LEF, GDS, Timing, …) are all generated for a given size configuration.

![An abstract diagram of word's placement](./Compiler/docs/img/word_concept.png)
![The custom placer's placement of the word, after just parsing the Verilog model](./Compiler/docs/img/word_placed.png)
![Same image, but with cell-level details](./Compiler/docs/img/word_detailed.png)

The layout generated from the compiler is highly compact (90%+ placement density) as the cells are placed on the floor plan using a custom placer. Moreover, the custom placer ensures that the routing will be relatively simple. The project will consider the creation of a custom router if automatic routing using open-source global and detailed routers do not give good results, though, they are, so far!

A beta version of the compiler is under the `Compiler/` directory. Check [its Readme](./Compiler/Readme.md) for more info. Currently, it can generate the following configurations:
- 128x32 (512 bytes) single port RAM with byte write enable.
- 512x32 (2kbytes) single port RAM with byte write enable.
- 2048x32 (8kbytes) single port RAM with byte write enable.

You can check out a Compiler-placed and routed RAM2048x32 (8 KiB) module [here](./Compiler/docs/img/8kb_layout.png).

# Data
<table>
  <tr>
    <th rowspan="2">Size<sup>1</sup></th> 
    <th colspan="2">OpenRAM<sup>2</sup></th> 
    <th colspan="2">DFFRAM Compiler</th> 
    <th colspan="2">DFFRAM/OpenLane</th> 
    <th colspan="2">RTL/OpenLane</th>
  </tr>
  <tr style="border-top:4px solid darkblue;">
    <td> Dim WxH (μm) </td> <td> Bit Density (bits/mm<sup>2</sup>) </td>
    <td> Dim WxH (μm) </td> <td> Bit Density (bits/mm<sup>2</sup>) </td>
    <td> Dim WxH (μm) </td> <td> Bit Density (bits/mm<sup>2</sup>) </td>
    <td> Dim WxH (μm) </td> <td> Bit Density (bits/mm<sup>2</sup>) </td>
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

<sup>1</sup> All support 32-bit word reads and 1, 2, and 4 bytes writes.  
<sup>2</sup> Values are based on the original layout produced by the compiler. OpenRAM macros are typically wrapped to be useful w/ automated PnR ASIC flows.

For more about the Handcrafted models, check the [Handcrafted Readme](./Handcrafted/docs/Readme.md).

# Usage
Check [Using Prflow](./Compiler/docs/md/Using%20Prflow.md).

# DFFRAM Compiler Routed Designs
A Byte
![A Byte; placed and routed](./Compiler/docs/img/byte_all_layers.png)

A Word
![A Word; placed and routed, metal only, no outline](./Compiler/docs/img/word_metal_only_no_outline.png)

8 Words
![8 Words; placed and routed](./Compiler/docs/img/8_routed_all_layers.png)

32 Words
![32 Words; placed and routed](./Compiler/docs/img/32_routed_all_layers.png)

128 Words
![128 Words; placed and routed](./Compiler/docs/img/128_routed_all_layers.png)

512 Words
![512 Words; placed and routed](./Compiler/docs/img/512_routed_all_layers.png)

1024 Words
![1024 Words; placed and routed](./Compiler/docs/img/1024_routed_all_layers.png)

2048 Words
![2048 Words; placed and routed](./Compiler/docs/img/2048_routed_all_layers.png)

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
