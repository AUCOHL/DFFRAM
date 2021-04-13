
PDK_PATH?=../../pdk
RTL_PATH=../../Compiler

.SUFFIXES:

PATTERN = tb_RAM32x32

all:  ${PATTERN:=.vcd}

%.vcd: %.vvp
	vvp $<
	echo "Done with VCD\n"

%.vvp: %.v
	iverilog -o $@ -DFUNCTIONAL -I $(PDK_PATH) -I $(RTL_PATH) \
	$<
	echo "Done with VVP\n"

%.v:
	python3 gen_tb.py ${PATTERN}
	echo "Done with V\n"

clean:
	rm -f *.vvp *.vcd *.out

.PHONY: clean all
