# -----------------------------------------------------------------------------
# Project 12 - Vivado non-project batch flow (owner: Ranajeet)
#
# Synthesizes, places and routes two designs out-of-context and writes
# utilization + timing reports for each:
#     systolic_top    (4x4 systolic array accelerator)
#     sequential_mac  (one-MAC baseline)
#
# Run from the repo root:
#     vivado -mode batch -nojournal -nolog -source synth/run_vivado.tcl
# Different FPGA part (optional):
#     vivado -mode batch -nojournal -nolog -source synth/run_vivado.tcl -tclargs xc7a100tcsg324-1
#
# Outputs (synth/reports/):
#     <TOP>_util.rpt       report_utilization
#     <TOP>_util_hier.rpt  report_utilization -hierarchical (per module)
#     <TOP>_timing.rpt     report_timing_summary
#     summary.txt          LUT / FF / DSP / BRAM / WNS / Fmax for both designs
# Checkpoints (synth/build/, git-ignored): <TOP>_routed.dcp, open in the GUI with
#     vivado synth/build/systolic_top_routed.dcp
# -----------------------------------------------------------------------------

# ---- FPGA part: change this line once the lab board is confirmed -----------
#   Basys 3        : xc7a35tcpg236-1
#   Nexys A7-100T  : xc7a100tcsg324-1
set PART xc7a35tcpg236-1
if {[llength $argv] > 0} { set PART [lindex $argv 0] }

set CLK_PERIOD 10.0   ;# ns, must match synth/constraints.xdc

# ---- paths (independent of the directory Vivado is started from) ------------
set SYNTH_DIR [file normalize [file dirname [info script]]]
set ROOT      [file normalize [file join $SYNTH_DIR ..]]
set RTL       [file join $ROOT rtl]
set XDC       [file join $SYNTH_DIR constraints.xdc]
set REPORTS   [file join $SYNTH_DIR reports]
set BUILD     [file join $SYNTH_DIR build]
file mkdir $REPORTS
file mkdir $BUILD

# ---- designs: top module -> only the rtl files it needs ---------------------
set DESIGNS [list \
    systolic_top   [list pe.v systolic_array.v input_buffer.v output_collector.v controller.v systolic_top.v] \
    sequential_mac [list sequential_mac.v] \
]

# Read one cell of the utilization table, e.g. "Slice LUTs", "DSPs".
proc util_value {rpt_text row} {
    foreach line [split $rpt_text "\n"] {
        if {[regexp "^\\|\\s*${row}\\*?\\s*\\|\\s*(\[0-9.\]+)" $line -> val]} {
            return $val
        }
    }
    return "n/a"
}

set summary [list]
lappend summary [format "Part: %s   Clock constraint: %.1f ns (%.0f MHz)" \
                 $PART $CLK_PERIOD [expr {1000.0 / $CLK_PERIOD}]]
lappend summary ""
lappend summary [format "%-16s %8s %8s %6s %6s %10s %12s" \
                 "Design" "LUTs" "FFs" "DSPs" "BRAM" "WNS (ns)" "Fmax (MHz)"]

foreach {TOP FILES} $DESIGNS {
    puts "\n================ $TOP on $PART ================"

    # fresh in-memory design for every top
    catch {close_design}
    catch {remove_files [get_files -quiet]}

    foreach f $FILES { read_verilog [file join $RTL $f] }
    read_xdc -mode out_of_context $XDC

    synth_design -top $TOP -part $PART -mode out_of_context
    opt_design
    place_design
    route_design

    set util_rpt   [file join $REPORTS ${TOP}_util.rpt]
    set timing_rpt [file join $REPORTS ${TOP}_timing.rpt]
    report_utilization    -file $util_rpt
    report_utilization    -hierarchical -file [file join $REPORTS ${TOP}_util_hier.rpt]
    report_timing_summary -file $timing_rpt

    # routed checkpoint, for opening in the Vivado GUI (screenshots); not committed
    write_checkpoint -force [file join $BUILD ${TOP}_routed.dcp]

    # ---- numbers for the summary table ----
    set fh [open $util_rpt r]; set txt [read $fh]; close $fh
    set luts [util_value $txt "Slice LUTs"]
    set ffs  [util_value $txt "Slice Registers"]
    set dsps [util_value $txt "DSPs"]
    set bram [util_value $txt "Block RAM Tile"]

    set path [get_timing_paths -quiet -delay_type max -max_paths 1 -nworst 1]
    if {[llength $path] > 0} {
        set wns  [get_property SLACK $path]
        set fmax [expr {1000.0 / ($CLK_PERIOD - $wns)}]
        set wns_s  [format "%.3f" $wns]
        set fmax_s [format "%.1f" $fmax]
    } else {
        set wns_s "n/a"; set fmax_s "n/a"
    }
    lappend summary [format "%-16s %8s %8s %6s %6s %10s %12s" \
                     $TOP $luts $ffs $dsps $bram $wns_s $fmax_s]
    puts "$TOP: LUT=$luts FF=$ffs DSP=$dsps BRAM=$bram WNS=$wns_s ns Fmax=$fmax_s MHz"
}

lappend summary ""
lappend summary "Fmax = 1000 / (CLK_PERIOD - WNS). Full details in the *_util.rpt and *_timing.rpt files."

set fh [open [file join $REPORTS summary.txt] w]
puts $fh [join $summary "\n"]
close $fh
puts "\n[join $summary "\n"]"
puts "\nReports written to $REPORTS"
