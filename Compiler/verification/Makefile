
PDK_PATH?=../../pdk
RTL_PATH=../sky130A/BB/experimental/model.v

.SUFFIXES:

.PRECIOUS: %.v %.vvp

PATTERN = tb_RAM32x32

all:  ${PATTERN:=.vcd}


help:
	@echo  ' you can call this make file like : make PATTERN=tb_RAM<WORDNUM>x32 '
	@echo  ' where WORDNUM is 8, 32, 128, 256, 512, 1024, 2048 .Default is 32, running it without'
	@echo  ' any arguments : make '
	@echo  ' is equivalent to make PATTERN=tb_RAM32x32 '
	@echo  '  clean           - Remove generated files'
	@echo  ''

%.vcd: %.vvp
	vvp $<

%.vvp: %.v
	iverilog -o $@ -DFUNCTIONAL -I $(PDK_PATH) \
	$< 

lint: ${PATTERN}.v
	./lint.sh $(TOP) $(PDK_PATH) $<

%.v:
	@echo ' Creating verilog tb from template ...'
	$(eval TOP := $(shell python3 gen_tb.py ${PATTERN}))
	@echo ' Done'



clean:
	rm -f *.vvp *.vcd *.out *.v *.log

.PHONY: clean all
