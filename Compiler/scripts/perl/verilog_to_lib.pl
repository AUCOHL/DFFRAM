#!/usr/bin/env perl
# Author: Sini Mukundan
# https://vlsi.pro/creating-lib-file-from-verilog/

use strict;

if ($#ARGV < 1 ) {
	print "usage: perl verilog_to_lib.pl <module>  <netlist> <outputfile> [tran[cap[signal_level]]]   \n";
    print "<netlist> <outputfile> <module> are all required";
	exit;
}

my $module = $ARGV[0] ;
my $tran = 2.5 ;
my $cap = 0.001;
my $signal_level = "VDD" ;

if(defined $ARGV[3]) {$tran = $ARGV[3];}
if(defined $ARGV[4]) {$cap = $ARGV[4];}
if(defined $ARGV[5]) {$signal_level = $ARGV[5];}

my $FF;
my $FO;
open $FF, "< $ARGV[1]" or die "Can't open $ARGV[0] : $!";
open $FO, ">$ARGV[2]" or die "Can't open $module.lib for write : $!";

my $db = createTopLevelDB(); 
createDotLib($db,$FO);

sub createDotLib
{
	my $topLevelDBRef = shift;
	my $FO = shift ;	
	### Header 
	print $FO "library\($topLevelDBRef->{'design'}->{'cell'}\) {\n";
	print $FO "\n /* unit attributes */\n";
	print $FO "  time_unit : \"1ns\"\;\n";
	print $FO "  voltage_unit : \"1V\"\;\n";
	print $FO "  current_unit : \"1uA\"\;\n";
	print $FO "  pulling_resistance_unit : \"1kohm\"\;\n";
	print $FO "  leakage_power_unit : \"1nW\"\;\n";
	print $FO "  capacitive_load_unit\(1,pf\)\;\n\n";
	foreach my $direction (keys(%{$topLevelDBRef->{'bus'}})) {
		foreach my $bus_type (keys %{$topLevelDBRef->{'bus'}->{$direction}}) {
			my @bus_width =  split(/_/, $bus_type); 
			my $bus_hi = $bus_width[1] ;
			my $bus_lo = $bus_width[2] ;
			my $bus_width = $bus_hi+1-$bus_lo;
			print $FO " type \($bus_type\) { \n";
			print $FO "   base_type : array ; \n" ;
    			print $FO "   data_type : bit  \n" ;;
    			print $FO "   bit_width : $bus_width   \n" ;;
    			print $FO "   bit_from : $bus_hi  \n" ;;
    			print $FO "   bit_to : $bus_lo ; \n" ;
    			print $FO "   downto : true ; \n" ;
    			print $FO " } \n" ;
		}
	}
	print $FO "\n  cell\($topLevelDBRef->{'design'}->{'cell'}\) {\n";
	foreach my $direction (keys(%{$topLevelDBRef->{'pins'}})) {
		foreach my $pin_name (@{$topLevelDBRef->{'pins'}->{$direction}}) {
			print $FO ("    pin\($pin_name\) { \n");
			print $FO ("\tdirection : $direction ;\n");
			if($direction eq "input") {
				print $FO ("\tmax_transition : $tran;\n");
			}
			print $FO ("\tcapacitance : $cap; \n");  	
			print $FO ("    } \n") ;
		}
	}
	foreach my $direction (keys(%{$topLevelDBRef->{'bus'}})) {
		foreach my $bus_type (keys %{$topLevelDBRef->{'bus'}->{$direction}}) {
			my @bus_width =  split(/_/, $bus_type); 
			my $bus_hi = $bus_width[1] ;
			my $bus_lo = $bus_width[2] ;
			foreach my $bus_name (@{$topLevelDBRef->{'bus'}->{$direction}{$bus_type}}) {
                                        chomp($bus_name);
				print "BUS $bus_name : $bus_type : $direction \n" ;
				print $FO ("    bus\($bus_name\) { \n");
				print $FO ("\tbus_type : $bus_type ;\n");
				print $FO ("\tdirection : $direction ;\n");
				if($direction eq "input") {
					print $FO ("\tmax_transition : $tran;\n");
				}	
				for(my $i=$bus_lo; $i<=$bus_hi; $i++) {
					print $FO ("\tpin\($bus_name\[$i\]\) { \n");
					print $FO ("\t\tcapacitance : $cap; \n");  
					print $FO ("\t} \n") ;
				}
				print $FO ("    } \n") ;
			}
		}
	}
	print $FO ("  } \n") ;
	print $FO ("} \n") ;
}

sub createTopLevelDB 
{
	my $find_top_module = 0; 
	my %topLevelDB = () ;
	my %pins = () ;
	my %bus = () ;
	my @input_pins ;
	my @output_pins ;
	my @inout_pins ;
	my @bus_types ; 
	my %input_bus = () ;
	my %output_bus = () ;
	my %inout_bus = () ;
	my %design = ();
	$design{'cell'} = $module; 
	$design{'tran'} = $tran; 
	$design{'cap'} = $cap; 
	$design{'signal_level'} = $signal_level; 
	while(my $line = <$FF>) {
		last if($find_top_module == 1);
		if($line=~/module\s+$module/) {
			$find_top_module = 1 ;
			while(my $line = <$FF>) {
				next if($line =~ "\s*//" );
				chomp($line);
				if ($line =~/input\s+/ ) {
					$line=~s/\s*input\s+//;
					$line=~s/;//;
					if($line =~/\[(\d+):(\d+)\]/) { 
						my $bus_type = "bus_$1_$2";
						$line=~s/\[(\d+):(\d+)\]//;
						my @line =  split(/,/, $line); 
						unless(grep {$_ eq $bus_type} @bus_types) {  
							push(@bus_types,$bus_type);
						}
						foreach my $pin (@line) {
							$pin=~s/\s+//;
							push(@{$input_bus{$bus_type}}, $pin );
						}
					}
					else {
						my @line =  split(/,/, $line); 
						foreach my $pin (@line) {
							$pin=~s/\s+//;
							push(@input_pins, $pin); 
						}
					}
				}
				if ($line =~/output\s+/ ) {
					$line=~s/\s*output\s+//;
					$line=~s/;//;
					if($line =~/\[(\d+):(\d+)\]/) { 
						my $bus_type = "bus_$1_$2";
						$line=~s/\[(\d+):(\d+)\]//;
						my @line =  split(/,/, $line); 
						unless(grep {$_ eq $bus_type} @bus_types) {  
							push(@bus_types,$bus_type);
						}
						foreach my $pin (@line) {
							$pin=~s/\s+//;
							push(@{$output_bus{$bus_type}}, $pin );
						}
					}
					else {
						my @line =  split(/,/, $line); 
						foreach my $pin (@line) {
							$pin=~s/\s+//;
							push(@output_pins, $pin); 
						}
					}

				}
				if ($line =~/inout\s+/ ) {
					$line=~s/\s*inout\s+//;
					$line=~s/;//;
					if($line =~/\[(\d+):(\d+)\]/) { 
						my $bus_type = "bus_$1_$2";
						$line=~s/\[(\d+):(\d+)\]//;
						my @line =  split(/,/, $line); 
						unless(grep {$_ eq $bus_type} @bus_types) {  
							push(@bus_types,$bus_type);
						}
						foreach my $pin (@line) {
							$pin=~s/\s+//;
							push(@{$inout_bus{$bus_type}}, $pin );
						}
					}
					else {
						my @line =  split(/,/, $line); 
						foreach my $pin (@line) {
							$pin=~s/\s+//;
							push(@inout_pins, $pin); 
						}
					}

				}

				last if($line=~/endmodule/);
			}

		}
	}
	$pins{'input'} = \@input_pins;
	$pins{'output'} = \@output_pins;
	$pins{'inout'} = \@inout_pins;
	$bus{'input'} = \%input_bus;
	$bus{'output'} = \%output_bus;
	$bus{'inout'} = \%inout_bus;
	$topLevelDB{'pins'} = \%pins;
	$topLevelDB{'bus'} = \%bus;
	$topLevelDB{'design'} = \%design;
	return \%topLevelDB;
}
