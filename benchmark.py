# Adapted from OpenLane by Donn.
#
# Copyright 2020 Efabless Corporation
# Copyright 2021 The American University in Cairo and the Cloud V Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import yaml
import glob
import queue
import threading
import subprocess
import pathlib

import click

class Design(object):
    def __init__(self, count, width, variant):
        self.count = count
        self.width = width
        self.variant = variant

    @staticmethod
    def from_yaml_object(yaml_object):
        return Design(yaml_object['count'], yaml_object['width'], yaml_object['variant'])

    @staticmethod
    def get_all():
        gha_string = open("./.github/workflows/main.yml").read()

        gha = yaml.safe_load(gha_string)

        jobs = gha['jobs']
        test_flow = jobs['test_flow']
        designs = test_flow['strategy']['matrix']['include']

        return [Design.from_yaml_object(design) for design in designs]


    @property
    def size(self):
        return f"{self.count}x{self.width}"

    @property
    def tag(self):
        return f"{self.size}_{self.variant}"

    def get_density(self, build_folder):
        density_file = glob.glob(os.path.join(build_folder, self.tag, "*.density.txt"))[0]
        density = float(open(density_file).read())
        return density

@click.group()
def start():
    pass

@click.command('run_designs')
@click.option("-w", "--worker-count", required=not os.getenv("WORKERS"), default=os.getenv("WORKERS"))
def run_designs(worker_count):
    worker_count = int(worker_count)
    
    designs = Design.get_all()

    q = queue.Queue()
    for design in designs:
        q.put(design)

    def run_design():
        while not q.empty():
            design = q.get(timeout=3)

            build_folder = os.path.join("./benchmark_build", design.tag)
            print(f"Started {design.tag}...")

            pathlib.Path(build_folder).mkdir(parents=True, exist_ok=True)
            stdout = open(os.path.join(build_folder, "stdout.log"), "w")
            stderr = open(os.path.join(build_folder, "stderr.log"), "w")
            try:
                subprocess.check_call([
                    "python3",
                    "./dffram.py",
                    "--variant", design.variant,
                    "--size", f"{design.count}x{design.width}",
                    "--base-build-dir", "./benchmark_build"
                ], stdout=stdout, stderr=stderr)

                print(f"Finished {design.tag}: Density {design.get_density('./benchmark_build')}.")
            except:
                print(f"Failed {design.tag}.")

            stdout.close()
            stderr.close()


    worker_threads = []
    for i in range(worker_count):
        worker_threads.append(threading.Thread(target=run_design))
        worker_threads[i].start()

    for i in range(worker_count):
        while worker_threads[i].is_alive() == True:
            worker_threads[i].join(100)
        print(f"Exiting thread {i}...")

start.add_command(run_designs)

@click.command("compile_densities")
def compile_densities():
    designs = Design.get_all()
    with open("./benchmark_build/densities.csv", "w") as f:
        print("tag,density", file=f)
        for design in designs:
            print(f"{design.tag},{design.get_density('./benchmark_build')}", file=f)
    
start.add_command(compile_densities)

if __name__ == "__main__":
    start()