#!/usr/bin/env python3
# -*- coding: utf8 -*-
# Copyright ©2020-2021 The American University in Cairo and the Cloud V Project.
#
# This file is part of the DFFRAM Memory Compiler.
# See https://github.com/Cloud-V/DFFRAM for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import sys
import uuid
import shutil
import pathlib
import tempfile
import subprocess

try:
    import click
    import yaml
except ImportError:
    print("You need to install click and pyyaml: python3 -m pip install click pyyaml")
    exit(os.EX_CONFIG)


tool_metadata_file_path = os.path.join(os.path.dirname(__file__), "tool_metadata.yml")
tool_metadata = yaml.safe_load(open(tool_metadata_file_path).read())


def mkdirp(path):
    return pathlib.Path(path).mkdir(parents=True, exist_ok=True)


@click.command()
def main():
    """
    Installs PDK to /usr/local/pdk/sky130A.

    Requires curl, tar, xzutils, may require sudo.
    """

    mkdirp("/usr/local/pdk")

    pdk = "/usr/local/pdk/sky130A"

    if os.path.exists(pdk) and len(os.listdir(pdk)) != 0:
        backup_path = pdk
        it = 0
        while os.path.exists(backup_path) and len(os.listdir(backup_path)) != 0:
            it += 1
            backup_path = f"/usr/local/pdk/sky130A.bk{it}"
        print(f"PDK installation already found at {pdk}, moving to {backup_path}...")
        shutil.move(pdk, backup_path)

    mkdirp("/usr/local/pdk/sky130A")

    tempdir = tempfile.gettempdir()
    download_path = os.path.join(tempdir, f"{uuid.uuid4()}.tar.xz")

    sky130_version = [tool for tool in tool_metadata if tool["name"] == "sky130"][0][
        "commit"
    ]
    open_pdks_version = [tool for tool in tool_metadata if tool["name"] == "open_pdks"][
        0
    ]["commit"]

    url = f"https://github.com/Cloud-V/sky130-builds/releases/download/{sky130_version}-{open_pdks_version}/sky130A.tar.xz"

    print(f"Downloading the pre-built PDK at {url}...")
    subprocess.check_call(["curl", "-L", "-o", download_path, url])

    print("Untarring...")
    subprocess.check_call(["tar", "-xJvf", download_path, "-C", pdk])


if __name__ == "__main__":
    try:
        main()
    except PermissionError as e:
        print("Encountered a permission error: Re-try as sudo", file=sys.stderr)
        print(e, file=sys.stderr)
        exit(os.EX_NOPERM)
