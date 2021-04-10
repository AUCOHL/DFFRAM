#!/bin/python3
import os
import subprocess
import pathlib
from subprocess import Popen
from pathlib import Path
from scripts_strings import *

designBuildFolderPath = pathlib.Path(BUILD_FOLDER)
designBuildFolderPath.mkdir(parents=True, exist_ok=True)
if not os.path.exists('./example_support'):
     print( "Untarring support files…")
     extractionCmd = "tar -xJf ./example_support.tar.xz"
     subprocess.run(extractionCmd.split())
p = pathlib.Path("./build/")
p.mkdir(parents=True, exist_ok=True)

def write_script_to_file(theScript, fileName):
    filePath = designBuildFolderPath / fileName
    with filePath.open("w", encoding="utf-8") as f:
        f.write(theScript)

def run_bash_string_cmd(cmdString):
    returnCode = subprocess.run(cmdString.split(),
            check=True).returncode
    if returnCode != 0:
        print("failure in cmd")
        print(cmdString.split())
        print(returnCode)
        exit(0)


def openlane(cmdString):
    DOCKER_TI_FLAG=""
    if DOCKER_INTERACTIVE == "1":
        DOCKER_TI_FLAG="-ti"
    dockerCmd = """docker run {}\
        -v {}:/mnt/dffram\
        -w /mnt/dffram/Compiler\
        efabless/openlane\
        {}""".format(DOCKER_TI_FLAG,
                    PROJECT_ROOT,
                    cmdString)
    run_bash_string_cmd(dockerCmd)

def flow():
    # 1. Synthesis
    # Not true synthesis, just elaboration.
    write_script_to_file(synthTclScript, "synth.tcl")
    write_script_to_file(synthShellScript, "synth.sh")
    openlane("bash {}/synth.sh".format(BUILD_FOLDER))
    # 2. Floorplan Initialization
    write_script_to_file(floorplanTclScript, "fp_init.tcl")
    openlane("openroad {}/fp_init.tcl".format(BUILD_FOLDER))
    # 3. PlaceRAM
    run_bash_string_cmd(placeDockerCmd)
    # Remove ports
    run_bash_string_cmd(removePortsCmd)
    run_bash_string_cmd(backupPlacedDesignCmd)
    run_bash_string_cmd(removeUnnecessaryPortsCmd)
    # 4. Verify Placement
    write_script_to_file(verifyTclScript, "verify.tcl")
    openlane("openroad {}/verify.tcl".format(BUILD_FOLDER))
    # 5. Attempt Routing
    write_script_to_file(routeTclScript, "route.tcl")
    write_script_to_file(trParams, "tr.params")
    openlane("openroad {}/route.tcl".format(BUILD_FOLDER))
    # 6. LVS
    write_script_to_file(lvsShellScript, "lvs.sh")
    openlane("bash {}/lvs.sh".format(BUILD_FOLDER))
    # Harden? # def -> gdsII (magic) and def -> lef (magic)
if __name__=="__main__":
    flow()
