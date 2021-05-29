
PDK_PATH?=../../pdk
RTL_PATH=../sky130A/BB/experimental/model.v

.SUFFIXES:

.PRECIOUS: %.v %.vvp

PATTERN = tb_RAM32x32

all:  ${PATTERN:=.vcd}


help:
	@echo  ' you can call this make file like : make PATTERN=tb_RAM<WORDNUM>x32 '
	@echo  ' where WORDNUM is 8, 32, 128, 512, default is 32, running it without'
	@echo  ' any arguments : make '
	@echo  ' is equivalent to make PATTERN=tb_RAM32x32 '
	@echo  '  clean           - Remove generated files'
	@echo  ''

%.vcd: %.vvp
	vvp $<

%.vvp: %.v
	# iverilog -s $(TOP) -o $@ -DFUNCTIONAL -I $(PDK_PATH)
	iverilog -o $@ -DFUNCTIONAL -I $(PDK_PATH) \
	$< 

lint: %.v
	iverilog  -s $(TOP) -Wall -DUNIT_DELAY="#1" -DFUNCTIONAL -I $(PDK_PATH) \
	$<

%.v:
	@echo ' Creating tb verilog from template ...'
	$(eval TOP := $(shell python3 gen_tb.py ${PATTERN}))
	@echo ' Done'



clean:
	rm -f *.vvp *.vcd *.out *.v *.log

.PHONY: clean all
