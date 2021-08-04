PATTERN = tb_RAM32x32
RCOUNT = 32
RWIDTH = 32

INCLUDE_PATHS=../platforms/sky130A/sky130_fd_sc_hd
RTL_PATH=../platforms/sky130A/sky130_fd_sc_hd/_building_blocks/ram/model.v
RF_PATH=../platforms/sky130A/sky130_fd_sc_hd/_building_blocks/rf/model.v

IVL_FLAGS= -DFUNCTIONAL $(addprefix -I ,$(INCLUDE_PATHS))
DFFRF_TB=tb_DFFRF$(RCOUNT)x$(RWIDTH)

.SUFFIXES:
.PRECIOUS: %.v %.vvp
all:  ${PATTERN:=.vcd}

tb_dffrf:
	$(eval RCOUNT=$(shell sh -c "echo "${PATTERN}" | grep -o -P '(?<=tb_DFFRF).*(?=x)'"))
	$(eval RWIDTH=$(shell sh -c " echo "${PATTERN}" | grep -o -P '(?<=x).*(?=_2R1W)'"))
	iverilog -o $(DFFRF_TB).vvp -DMODEL_FILEPATH=$(RF_PATH) -DRCOUNT=$(RCOUNT) -DRWIDTH=$(RWIDTH) \
		$(IVL_FLAGS) dffrf_tb.v
	vvp $(DFFRF_TB).vvp

%.vcd: %.vvp
	vvp $<

%.vvp: %.v
	iverilog -o $@ $(IVL_FLAGS) $< 

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
