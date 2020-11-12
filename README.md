# DFFRAM
Standard Cell Library based Memory Compiler using DFF cells

The objective of this project is to develop DFF-based RAM and Register File (RegF) compiler that utilizes standard cell libraries following a standard ASIC implementation approach. The compiler generates different views (HDL netlist, HDL functional models, LEF, GDS, Timing, …) for a given configuration set. 

The layout generated from the compiler will be highly compacted (we target over 95% placement density) as the cells are placed on the floor plan using a custom placer. Moreover, the custom placer ensures that the routing will be a seamless one. The project will consider the creation of a custom router if automatic routing using open-source global and detailed routers does not give good results. 

Currenly, the repo has only a handcrafted parameterized memory (1, 2 or 4 kbytes) targeting the the SKY130 PDK. Also, it contains all the building blocks and a self-checking testbench. 
