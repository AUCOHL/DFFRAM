
PDK_PATH?=../../pdk
RTL_PATH=../Models

.SUFFIXES:

PATTERN = tb_RAM32x32

all:  ${PATTERN:=.vcd}

%.vvp: %.v
	iverilog -o $@ -DFUNCTIONAL -I $(PDK_PATH) -I $(RTL_PATH) \
	$< 

%.vcd: %.vvp
	vvp $<

clean:
	rm -f *.vvp *.vcd *.out

.PHONY: clean all