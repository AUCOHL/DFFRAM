#!/usr/bin/perl
use warnings;
use strict;
my $net = "";
my $cell = "";
while(<>){
	# print $_;
   	if ( m/Net/ ){
		$net = $_;
	} elsif ( m/sky/ ){
		$cell = $_;
	} elsif ( m/\*/ ){
   		print "$net$cell$_";
	}
}
