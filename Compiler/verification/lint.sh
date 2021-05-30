#!/bin/sh
# $1 top module
# $2 pdk path
# $3 verilog file

iverilog -Wall -s $1 -DUNIT_DELAY="#1" -DFUNCTIONAL -I $2 $3 2> linterrs
ERRS=$(grep -v timescale linterrs)
rm linterrs
if [ !ERRS ]
then
    exit 0
else
    exit 1
fi

