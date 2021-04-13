# PlaceRAM
This is the custom placer for the SKY130A DFFRAM compiler. At the moment it is capable pf placing the cells of DFFRAM 32x32 block. A sample output is given below:
![Klayout showing the 32x32 module placed](./docs/img/32x32_placed.png)

# Dependencies
You can use Docker to substitute all of these dependencies, but:

* Python 3.8+ with PIP
  * PlaceRAM makes heavy use of `:=` and is unrepentant.
* Opendbpy
  * Installation instructions can be found [here](./docs/md/Using%20Opendbpy.md).
* PIP package `click`: `pip3 install click`.

## Recommended
* Docker (see above)
* Klayout (to view the final result)

# Structure
* `BB.v` contains the building blocks used by the compiler
* `example/` contains support files.
* `placeram/` contains the core Python script.
* `example.sh` is a flow going from building blocks to LVS.
  * `prflow/` contains a Python replacement (runnable via `example_py.sh`), albeit a work in progress. The idea is to make prflow more… configurable than the shell script.

# Documentation
1. [Using Opendbpy](./md/Using%20Opendbpy.md)
2. [How PlaceRAM Works](./md/How%20PlaceRAM%20Works.md)
