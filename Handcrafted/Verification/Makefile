
PDK_PATH?=/ef/tech/SW/sky130A
RTL_PATH=../Models

.SUFFIXES:

PATTERN = tb_DFFRAM

all:  ${PATTERN:=.vcd}

%.vvp: %.v
	iverilog -DFUNCTIONAL -I $(PDK_PATH) -I $(RTL_PATH) \
	$< -o $@

%.vcd: %.vvp
	vvp $<

clean:
	rm -f *.vvp *.vcd *.out

.PHONY: clean all