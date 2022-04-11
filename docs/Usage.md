# Using DFFRAM
DFFRAM is based around two Python modules: `dffram` and `placeram`.

`dffram.py` is a relatively self-contained flow that uses Openlane and other technologies to place, route and harden RAM. `dffram.py` runs on the host machine.

`placeram` is a custom placer using OpenROAD's Python interface. It places DFFRAM RAM/RF designs in a predetermined structure to avoid a lengthy and inefficient manual placement process for RAM. Unlike `dffram.py`, `placeram` runs in a Docker container to avoid mandating an OpenROAD dependency (which is huge.)

# Dependencies
* A Unix-like Operating System
  * Use the Windows Subsystem for Linux on Windows (which I use)
* The Skywater 130nm PDK
  * See [Getting Sky130](./md/Getting%20Sky130.md)
* Docker Container
* Python 3.6+ with PIP
  * PIP packages `click` and `pyyaml`: `python3 -m pip install click pyyaml`

## Recommended
* Klayout (to view the final result)

# Basic
```sh
export PDK_ROOT=/usr/local/pdk
git clone https://github.com/Cloud-V/DFFRAM 
cd DFFRAM
python3 -m pip install -r requirements.txt
./dffram.py -s 8x32 # <8-2048>x<8-64>
```
# Run on Google Colab 
DFFRAM can run on Google Colab. 

An example Notebook can be found [here](https://colab.research.google.com/github/Cloud-V/DFFRAM/blob/main/dffram.ipynb).
# Local Installation (Linux Only)
## Installing Conda 

1) Download the installer from [here](https://docs.conda.io/en/latest/miniconda.html#linux-installers).
2) Install Conda by running the following command:
```
bash Miniconda3-latest-Linux-x86_64.sh
```
## Run DFFRAM

1) Create and activate the virtual enviroment 
```
conda env create -f environment.yml
conda activate dffram
env NO_CHECK_INSTALL=1
env TCLLIBPATH=/usr/share/tcltk

```
2) Invoke DFFRAM Compiler


```
./dffram.py --using-local-openlane <local_openlane_path> --pdk-root /usr/local/share/pdk -s 32x32 -b ::rf -v 2R1W

```

# Advanced
The compilation flow at a minimum needs two options: the building blocks and the size.

```sh
export PDK_ROOT=/usr/local/pdk
./dffram.py -b sky130A:sky130_fd_sc_hd:ram -s 8x32
```

The building block set `pdk:scl:name` corresponds to `./platforms/<pdk>/<scl>/_building_blocks/<name>/model.v`. Building block sets are fundamentally similar with a number of exceptions, most importantly, the SCL used and supported sizes.

## Options
For a full list of options, please invoke:
```sh
./dffram.py --help
```

### Secret Menu
DFFRAM supports a number of secret options you can use to further customize your experience. They are all passed as environment variables:

Variable Name|Effect
-|-
PRFLOW_CREATE_IMAGE|If set to any value, a step after placement and routing that creates an image with Klayout is added. It's good for sanity checks.
FORCE_ACCEPT_SIZE|DFFRAM checks that you are not using a size not officially marked supported as available by a certain building block set. If this environment variable is set to any value, the check is bypassed.
FORCE_DESIGN_NAME|Design names are found based on the size. If you'd like to force dffram to use a specific design name instead, set this environment variable to that name.


# Appendices
- [Appendix A: Using Opendbpy](./md/Using%20Opendbpy.md)
- [Appendix B: How PlaceRAM Works](./md/How%20PlaceRAM%20Works.md)