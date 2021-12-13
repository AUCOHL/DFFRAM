#!/usr/bin/env tclsh
source $::env(ENV_FILE)
if { [catch {exec >@stdout 2>@stderr {*}$argv} err]} {
    puts stderr $err
    exit -1
}
exit