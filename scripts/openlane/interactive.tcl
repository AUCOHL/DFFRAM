

package require openlane
set script_dir [file dirname [file normalize [info script]]]

prep -design $script_dir

set ::env(LIB_SYNTH_COMPLETE_NO_PG) [list]
foreach lib $::env(LIB_SYNTH_COMPLETE) {
    set fbasename [file rootname [file tail $lib]]
    set lib_path [index_file $::env(synthesis_tmpfiles)/$fbasename.no_pg.lib]
    convert_pg_pins $lib $lib_path
    lappend ::env(LIB_SYNTH_COMPLETE_NO_PG) $lib_path
}

set_def $::env(INITIAL_DEF)
set_netlist $::env(INITIAL_NETLIST)
set ::env(CURRENT_SDC) $::env(INITIAL_SDC)

run_power_grid_generation
run_routing
run_magic
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

proc save_final_views {args} {
    set options {
        {-save_path optional}
    }
    set flags {}
    parse_key_args "save_final_views" args arg_values $options flags_map $flags

    set arg_list [list]


    # If they don't exist, save_views will simply not copy them
    lappend arg_list -lef_path $::env(signoff_results)/$::env(DESIGN_NAME).lef
    lappend arg_list -gds_path $::env(signoff_results)/$::env(DESIGN_NAME).gds
    lappend arg_list -mag_path $::env(signoff_results)/$::env(DESIGN_NAME).mag
    lappend arg_list -maglef_path $::env(signoff_results)/$::env(DESIGN_NAME).lef.mag
    lappend arg_list -spice_path $::env(signoff_results)/$::env(DESIGN_NAME).spice
    # Guaranteed to have default values
    lappend arg_list -def_path $::env(CURRENT_DEF)
    lappend arg_list -verilog_path $::env(CURRENT_NETLIST)

    # Not guaranteed to have default values
    if { [info exists ::env(SPEF_TYPICAL)] } {
        lappend arg_list -spef_path $::env(SPEF_TYPICAL)
    }
    if { [info exists ::env(CURRENT_SDF)] } {
        lappend arg_list -sdf_path $::env(CURRENT_SDF)
    }
    if { [info exists ::env(CURRENT_SDC)] } {
        lappend arg_list -sdc_path $::env(CURRENT_SDC)
    }

    # Add the path if it exists...
    if { [info exists arg_values(-save_path) ] } {
        lappend arg_list -save_path $arg_values(-save_path)
    }

    # Aaand fire!
    save_views {*}$arg_list

}

save_final_views -save_path $::env(PRODUCTS_PATH)

calc_total_runtime
save_state
generate_final_summary_report
check_timing_violations
