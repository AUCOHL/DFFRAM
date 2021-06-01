
INCLUDE_PATHS=../sky130A/sky130_fd_sc_hd
RTL_PATH=../sky130A/BB/ram/model.v

IVL_FLAGS= -DFUNCTIONAL $(addprefix -I ,$(INCLUDE_PATHS))

.SUFFIXES:

.PRECIOUS: %.v %.vvp

PATTERN = tb_RAM32x32

all:  ${PATTERN:=.vcd}

help:
	@echo  ' Usage: make [PATTERN=tb_RAM<WORDNUM>x32] '
	@echo  ' WORDNUM is 8, 32, 128, 256, 512, 1024, 2048. (Default: 32)'
	@echo  '  clean           - Remove generated files'
	@echo  ''

%.vcd: %.vvp
	vvp $<

%.vvp: %.v
	iverilog -o $@ $(IVL_FLAGS) $< 

lint: ${PATTERN}.v
	iverilog -Wall -s $(PATTERN) -DUNIT_DELAY="#1" $(IVL_FLAGS) $(PATTERN).v 2> lint.rpt
	@exit $(shell grep -cv timescale lint.rpt)

%.v: gen_tb.py tb_template.py
	@echo ' Creating verilog tb from template ...'
	$(eval TOP := $(shell python3 gen_tb.py ${PATTERN}))
	@echo ' Done'

clean:
	rm -f *.vvp *.vcd *.out *.v *.log

.PHONY: clean all
