# Overview of the steps of the flow
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