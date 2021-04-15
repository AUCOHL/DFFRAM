#!/bin/python3
from .scripts import *

import os
import shlex
import subprocess
import pathlib
import re

build_folder = pathlib.Path(BUILD_FOLDER)
build_folder.mkdir(parents=True, exist_ok=True)

if not os.path.exists('./example_support'):
     print("Untarring support files…")
     extractionCmd = "tar -xJf ./example/example_support.tar.xz"
     subprocess.run(extractionCmd.split())
p = pathlib.Path("./build/")
p.mkdir(parents=True, exist_ok=True)

def remove_all_ports_from_placed(fileName, newFileName):
    with open(fileName, 'r') as f, open(newFileName, "w+") as fout:
        data = f.read()
        data = data.replace('+ PORT', '')
        fout.write(data)

def write_script_to_file(theScript,
        fileName,
        build_folder=build_folder):
    filePath = build_folder / fileName
    print("writing file : ", filePath)
    with filePath.open("w", encoding="utf-8") as f:
        f.write(theScript)

def run_bash_string_cmd(cmdString, shell=False):
    result = subprocess.run(
        shlex.split(cmdString),
        shell=shell
    )
    if result.returncode != 0:
        print("Command '{}' failed with exit code {}.".format(cmdString, result.returncode))
        exit(-1)

def openlane(cmdString):
    DOCKER_TI_FLAG=""
    if DOCKER_INTERACTIVE == "1":
        DOCKER_TI_FLAG="-ti"
    dockerCmd = "docker run {} -v {}:/mnt/dffram -w /mnt/dffram/Compiler efabless/openlane {}".format(
        DOCKER_TI_FLAG,
        PROJECT_ROOT,
        cmdString
    )
    run_bash_string_cmd(dockerCmd)

def main():
    # 1. Synthesis
    # Not true synthesis, just elaboration.
    write_script_to_file(synthTclScript, "synth.tcl")
    write_script_to_file(synthShellScript, "synth.sh")
    openlane("bash {}/synth.sh".format(BUILD_FOLDER))

    # 2. Floorplan Initialization
    write_script_to_file(floorplanTclScriptFilled, "fp_init.tcl")
    openlane("openroad {}/fp_init.tcl".format(BUILD_FOLDER))

    # 3. PlaceRAM
    run_bash_string_cmd(placeDockerCmd)
    ## Remove ports
    run_bash_string_cmd(removePortsCmd)
    run_bash_string_cmd(backupPlacedDesignCmd)
    remove_all_ports_from_placed(
            "{}/{}.placed.def.ref".format(BUILD_FOLDER, DESIGN),
            "{}/{}.placed.def".format(BUILD_FOLDER, DESIGN))

    # 4. Verify Placement
    write_script_to_file(verifyTclScript, "verify.tcl")
    openlane("openroad {}/verify.tcl".format(BUILD_FOLDER))

    # 5. Attempt Routing
    write_script_to_file(routeTclScript, "route.tcl")
    write_script_to_file(trParams, "tr.param")
    openlane("openroad {}/route.tcl".format(BUILD_FOLDER))

    # 6. LVS
    write_script_to_file(lvsTclScript, "lvs.tcl")
    write_script_to_file(lvsShellScript, "lvs.sh")
    openlane("bash {}/lvs.sh".format(BUILD_FOLDER))

    # TODO: Harden?
    ## def -> gdsII (magic) and def -> lef (magic)
