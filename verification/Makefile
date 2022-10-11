PATTERN = tb_RAM32x32

PDK_ROOT ?= ../pdks
PDK ?= sky130A
SCL ?= sky130_fd_sc_hd
export PDK_ROOT

INCLUDE_PATHS=../platforms/${PDK}/${SCL}
DEFINITIONS_FILE=../platforms/${PDK}/${SCL}/block_definitions.v

IVL_FLAGS= -DFUNCTIONAL $(addprefix -I ,$(INCLUDE_PATHS))

.SUFFIXES:
.PRECIOUS: %.v %.vvp
all:  ${PATTERN:=.vcd}

%.vcd: %.vvp
	vvp $<

%.vvp: %.v
	iverilog -o $@ $(IVL_FLAGS) $(DEFINITIONS_FILE) $< 

# $$ = delayed evaluation
lint: ${PATTERN}.v
	iverilog -Wall -s $(PATTERN) -DUNIT_DELAY="#1" $(IVL_FLAGS) $(PATTERN).v 2> lint.rpt
	@exit $$(grep -cv timescale lint.rpt)

%.v: gen_tb.py tb_template.py
	@echo 'Generating TB from template...'
	python3 gen_tb.py ${PATTERN}
	@echo 'Done.'

.PHONY: help clean
help:
	@echo  'Usage: make [PATTERN=tb_RAM<WORDNUM>x32] '
	@echo  'WORDNUM is 8, 32, 128, 256, 512, 1024, 2048. (Default: 32)'
	@echo  'clean           - Remove generated files'
	@echo  ''

clean:
	rm -f *.vvp *.vcd *.out *.v *.log *.rpt
