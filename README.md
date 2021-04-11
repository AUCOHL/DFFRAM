# DFFRAM Compiler
![CI Badge](https://github.com/Cloud-V/DFFRAM/actions/workflows/main.yml/badge.svg?branch=main)

Standard Cell Library based Memory Compiler using DFF cells.

The objective of this project is to develop DFF-based RAM and Register File (RegF) compiler that utilizes standard cell libraries following a standard ASIC implementation approach. The compiler generates different views (HDL netlist, HDL functional models, LEF, GDS, Timing, …) for a given configuration set. 

The layout generated from the compiler will be highly compacted (we target over 95% placement density) as the cells are placed on the floor plan using a custom placer. Moreover, the custom placer ensures that the routing will be relatively simple. The project will consider the creation of a custom router if automatic routing using open-source global and detailed routers does not give good results, though, they are, so far!

## Compiler
A beta version of the compiler is under the `Compiler/` directory. Check [its Readme](./Compiler/Readme.md) for more info.

## Handcrafted
Until the compiler is fully ready, you may harden pre-existing handcrafted designs using Openlane.  Here is a high-level view of the improvement over RTL synthesis:

| Size  | No of Instances (*Handcrafted*/RTL) | Placement Density (*Handcrafted*/RTL) | Dimensions X (µm) x Y (µm) (*Handcrafted*/RTL) |
| -     | -                                   | -                                     | -                                              |
| 1KiB  | *19,897* vs 51,972                  | *87.2%* vs 61%                        | *425	x 820* vs 1,050 x 1,060                  |
| 2KiB* | *40,554* vs 103,933                 | *84.8%* vs 61%                        | *1,210 x 610* vs 1,470 x 1,481                 |
| 4KiB  | *81,044* vs 207,822                 | *84.8%* vs 61%                        | *1,628 x 911* vs 2,074 x 2,085                 |

\*  OpenLANE did not produce a clean GDSII for the RTL.

For more about the Handcrafted models, check the [Handcrafted Readme](./Handcrafted/docs/Readme.md).

# ⚖️ License
Copyright ©2021-present The American University in Cairo and the Cloud V Project. You may use and redistribute this code under the Apache 2.0 license. See 'LICENSE'.

