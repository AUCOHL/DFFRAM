# DFFRAM Compiler
## Dependencies
You can use Docker to substitute all of these dependencies, but, in case of a native install:

* Python 3.8+ with PIP
  * PlaceRAM makes heavy use of `:=` and is unrepentant.
  * It might be repentant if we need to integrate it into Openlane or something.
* Opendbpy
  * Installation instructions can be found [here](./docs/md/Using%20Opendbpy.md).
* PIP package `click`: `pip3 install click`.

### Recommended
* Docker (see above)
* Klayout (to view the final result)

## Structure
* `platforms/` contains PDK-specific files:
  * `<pdk-name>/`
    * `BB/` contains a hierarchy of building blocks supported by the compiler.
* `placeram/` contains the core Python custom placer.
* `prflow.py` is the compilation flow going from building blocks to LVS.

## Table of Contents
<!-- Note: Yes, ordered lists mandate all of them to be 1. in markdown. -->
1. [Using Prflow](./md/Using%20Prflow.md)
1. [Using Opendbpy](./md/Using%20Opendbpy.md)
1. [How PlaceRAM Works](./md/How%20PlaceRAM%20Works.md)
