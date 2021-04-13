
PDK_PATH?=../../pdk
RTL_PATH=..

.SUFFIXES:

PATTERN = tb_RAM32x32

all:  ${PATTERN:=.vcd}

%.vcd: %.vvp
	vvp $<

%.vvp: %.v
	iverilog -o $@ -DFUNCTIONAL -I $(PDK_PATH) -I $(RTL_PATH) \
	$<

%.v:
	python3 gen_tb.py ${PATTERN}

clean:
	rm -f *.vvp *.vcd *.out

.PHONY: clean all
