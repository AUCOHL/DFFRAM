
PDK_PATH?=../../pdk
RTL_PATH=..

.SUFFIXES:

PATTERN = tb_RAM32x32

all:  ${PATTERN:=.vcd}

# lint: %.v
# 	iverilog -s -o $@ -DFUNCTIONAL -I $(PDK_PATH) -I $(RTL_PATH) \
# 	$<

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
	iverilog -o $@ -DFUNCTIONAL -I $(PDK_PATH) -I $(RTL_PATH) \
	$<

%.v:
	python3 gen_tb.py ${PATTERN}

clean:
	rm -f *.vvp *.vcd *.out

.PHONY: clean all
