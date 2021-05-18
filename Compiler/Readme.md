# DFFRAM Compiler
This is the custom placer for the SKY130A DFFRAM compiler. At the moment it is capable of placing the cells of DFFRAM 2048x32 block. A sample output is given below:
![Klayout showing the 2048x32 module placed](./docs/img/8kb_layout.png)

# Dependencies
You can use Docker to substitute all of these dependencies, but, in case of a native install:

* Python 3.8+ with PIP
  * PlaceRAM makes heavy use of `:=` and is unrepentant.
* Opendbpy
  * Installation instructions can be found [here](./docs/md/Using%20Opendbpy.md).
* PIP package `click`: `pip3 install click`.

## Recommended
* Docker (see above)
* Klayout (to view the final result)

# Structure
* `docs/` contains documentation files. (😨)
* `sky130A/` contains PDK-specific files:
  * `BB/` contains a list of building blocks supported by the compiler.
  * `assemble_support.sh` assembles a support tarball with a subset of the PDK…
  * … and `support.tar.xz` is the aforementioned tarball.
* `placeram/` contains the core Python utility.
* `prflow.py` is a flow going from building blocks to LVS.

# Documentation
1. [Using placeram as part of the flow](https://github.com/Cloud-V/DFFRAM#using-the-compiler-wip)
1. [Using Opendbpy](./docs/md/Using%20Opendbpy.md)
2. [How PlaceRAM Works](./docs/md/How%20PlaceRAM%20Works.md)
