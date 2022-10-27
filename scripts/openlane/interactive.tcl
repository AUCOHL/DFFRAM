

package require openlane
set script_dir [file dirname [file normalize [info script]]]
prep -design $script_dir -ignore_mismatches

set ::env(LIB_SYNTH_COMPLETE_NO_PG) [list]
foreach lib $::env(LIB_SYNTH_COMPLETE) {
    set fbasename [file rootname [file tail $lib]]
    set lib_path [index_file $::env(synthesis_tmpfiles)/$fbasename.no_pg.lib]
    convert_pg_pins $lib $lib_path
    lappend ::env(LIB_SYNTH_COMPLETE_NO_PG) $lib_path
}

set_odb $::env(INITIAL_ODB)

set ::env(INITIAL_DEF) [file rootname $::env(CURRENT_ODB)].def
exec echo { read_db $::env(CURRENT_ODB) write_def $::env(INITIAL_DEF) } | $::env(OPENROAD_BIN) -exit

set ::env(CURRENT_SDC) $::env(INITIAL_SDC)

if { $::env(DIODE_INSERTION_STRATEGY) == 3 } {
    puts "Removing fill cells..."
    puts [exec $::env(OPENROAD_BIN) -python ./scripts/openroad/unplace.py\
        --from-fills-file "./platforms/$::env(PDK)/fill_cells.yml"\
        --exclude-tap\
        $::env(CURRENT_ODB)]
}

run_power_grid_generation

global_routing

if { $::env(DIODE_INSERTION_STRATEGY) == 3 } {
    # https://github.com/The-OpenROAD-Project/OpenLane/pull/1453
    set ::env(FILL_INSERTION) {1}
    ins_fill_cells
}

detailed_routing

run_magic
run_parasitics_sta
if {  [info exists ::env(ENABLE_KLAYOUT) ] } {
    if { ($::env(ENABLE_KLAYOUT) == 1)  } {
        run_klayout
        run_klayout_gds_xor
    }
}

run_magic_spice_export
run_lvs
run_magic_drc
if {  [info exists ::env(ENABLE_KLAYOUT) ] } {
    if { ($::env(ENABLE_KLAYOUT) == 1)  } {
        run_klayout_drc
    }
}
run_antenna_check
if {  [info exists ::env(ENABLE_CVC) ] } {
    if { ($::env(ENABLE_CVC) == 1)  } {
        run_lef_cvc
    }
}

save_final_views -save_path $::env(PRODUCTS_PATH)

calc_total_runtime
save_state
generate_final_summary_report
check_timing_violations
