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
    <th colspan="2">Handcrafted</th> 
    <th colspan="2">RTL</th>
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
    <td> TBD </td> <td> TBD </td>
  </tr>
  <tr>
    <td> 1 kbytes </td>
    <td> 386 x 456 </td> <td> 46,541 </td>
    <td> TBD </td> <td> TBD </td>
    <td> 425 x 820 </td> <td> 23,506 </td>
    <td> 1,050 x 1,060 </td> <td> 7,360 </td>
  </tr>
  <tr>
    <td> 2 kbytes </td>
    <td> 659.98 x 398.18  </td> <td> 62,372 </td>
    <td> 793.5 x 783.36 </td> <td> 26,358 </td>
    <td> 1,210 x 621 </td> <td> 21,789 </td>
    <td> TBD </td> <td> TBD </td>
  </tr>
  <tr>
    <td> 4 kbytes </td>
    <td> 670.86 x 651.14 </td> <td> 75,014 </td>
    <td> TBD </td> <td> TBD </td>
    <td> 1,628 x 911 </td> <td> 22,094 </td>
    <td> 2,074 x 2,085 </td> <td> 7,578 </td>
    
  </tr>
  <tr>
    <td> 8 kbytes </td>
    <td> N/A </td> <td> N/A </td>
    <td> 1,589 x 1,572</td> <td> 26,229 </td>
    <td> TBD </td> <td> TBD </td>
    <td> TBD </td> <td> TBD </td>
  </tr>
</table>

\* Values are based on original layout produced by teh compiler. OpenRAM macros are typically wrapped to be useful w/ automated PnR ASIC flows.

## Handcrafted
Until the compiler is fully ready, you may harden pre-existing handcrafted designs using Openlane.  Here is a high-level view of the improvement over RTL synthesis:

| Size  | No of Instances (*Handcrafted*/RTL) | Placement Density (*Handcrafted*/RTL) | Dimensions X (µm) x Y (µm) (*Handcrafted*/RTL) |
| -     | -                                   | -                                     | -                                              |
| 1KiB  | *19,897* vs 51,972                  | *87.2%* vs 61%                        | *425	x 820* vs 1,050 x 1,060                  |
| 2KiB* | *40,554* vs 103,933                 | *84.8%* vs 61%                        | *1,210 x 610* vs 1,470 x 1,481                 |
| 4KiB  | *81,044* vs 207,822                 | *84.8%* vs 61%                        | *1,628 x 911* vs 2,074 x 2,085                 |

\* All support 32-bit word reads and 1, 2,and 4 bytes writes.
\*\*  OpenLANE did not produce a clean GDSII for the RTL.

For more about the Handcrafted models, check the [Handcrafted Readme](./Handcrafted/docs/Readme.md).

# ⚖️ License
Copyright ©2021-present The American University in Cairo and the Cloud V Project. You may use and redistribute this code under the Apache 2.0 license. See 'License'.

