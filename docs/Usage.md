# Using DFFRAM
DFFRAM is based around `placeram`, a Python module, and `dffram.py`, a Python
application.

`placeram` is a custom placer using OpenROAD's Python interface.
It places DFFRAM RAM/RF designs in a predetermined structure to avoid a lengthy
and inefficient manual placement process for RAM.

`dffram.py` is an OpenLane-based flow that performs every step of hardening
the RAM modules from elaboration to GDS-II stream out. It incorporates `placeram`.

# Dependencies
* macOS or Linux
* The Nix Package Manager

## Installing Nix

Please follow the LibreLane installation guide for Nix:

https://librelane.readthedocs.io/en/latest/getting_started/common/nix_installation/index.html

# Basic
```sh
git clone https://github.com/Cloud-V/DFFRAM 
cd DFFRAM
nix develop github:librelane/librelane/3.0.0dev25
./dffram.py 8x32 # <8-2048>x<8-64>
```

# Advanced
The compilation flow has four main arguments:
  * `--pdk`: The PDK
  * `--scl`: The Standard Cell Library
  * `--building-blocks`: The building blocks.
  * The Size (passed without a flag)

The building block full set `pdk:scl:blocks` corresponds to `./platforms/<pdk>/<scl>/_building_blocks/<name>/model.v`. Building block sets are fundamentally similar with a number of exceptions, most importantly, the SCL used and supported sizes.

For example:

```sh
./dffram.py -p sky130A -s sky130_fd_sc_hd -b ram 8x32
```


## Options
For a full list of options, please invoke:
```sh
./dffram.py --help
```

### Secret Menu
DFFRAM supports a number of secret options you can use to further customize your experience. They are all passed as environment variables:

Variable Name|Effect
-|-
FORCE_ACCEPT_SIZE|DFFRAM checks that you are not using a size not officially marked supported as available by a certain building block set. If this environment variable is set to any value, the check is bypassed.
FORCE_DESIGN_NAME|Design names are found based on the size. If you'd like to force dffram to use a specific design name instead, set this environment variable to that name.


# Appendices
- [Appendix A: Using Opendbpy](./md/Using%20Opendbpy.md)
- [Appendix B: How PlaceRAM Works](./md/How%20PlaceRAM%20Works.md)
