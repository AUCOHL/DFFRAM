# -*- coding: utf8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright ©2020-2025, The American University in Cairo
# Copyright ©2023 Efabless Corporation
import os
import math
from typing import List
from decimal import Decimal

import yaml
from librelane.config import Variable
from librelane.logging import warn
from librelane.state import DesignFormat
from librelane.steps import OpenROAD, Odb


class PlaceRAM(Odb.OdbpyStep):
    id = "DFFRAM.PlaceRAM"

    config_vars = [
        Variable(
            "RAM_SIZE",
            str,
            "The size of the RAM macro being hardened the format {words}x{bits}",
        ),
        Variable(
            "BUILDING_BLOCKS",
            str,
            "The set of building blocks being used.",
            default="ram",
        ),
    ]

    def get_script_path(self):
        return "placeram"

    def get_command(self) -> List[str]:
        raw = super().get_command() + [
            "--building-blocks",
            f"{self.config['PDK']}:{self.config['STD_CELL_LIBRARY']}:{self.config['BUILDING_BLOCKS']}",
            "--size",
            self.config["RAM_SIZE"],
        ]
        raw.insert(raw.index("placeram"), "-m")
        return raw


class Floorplan(OpenROAD.Floorplan):
    id = "DFFRAM.Floorplan"

    outputs = [
        DesignFormat.ODB,
    ]

    config_vars = [
        var
        for var in OpenROAD.Floorplan.config_vars
        if var.name not in ["FP_SIZING", "CORE_AREA", "DIE_AREA"]
    ] + [
        Variable(
            "HORIZONTAL_HALO",
            type=Decimal,
            description="The space between the horizontal edges of the die area and the core area in microns.",
            units="µm",
            default=2.5,
        ),
        Variable(
            "VERTICAL_HALO",
            type=Decimal,
            description="The space between the vertical edges of the die area and the core area in microns.",
            units="µm",
            default=2.5,
        ),
        Variable(
            "MINIMUM_HEIGHT",
            type=Decimal,
            description="A minimum height to be applied",
            default=0,
            units="µm",
        ),
    ]

    def run(self, state_in, **kwargs):
        min_height = self.config["MINIMUM_HEIGHT"]

        core_width = Decimal(
            state_in.metrics.get("dffram__suggested__core_width") or 20000
        )
        core_height = Decimal(
            state_in.metrics.get("dffram__suggested__core_height") or 20000
        )

        horizontal_halo = self.config["HORIZONTAL_HALO"]
        vertical_halo = self.config["VERTICAL_HALO"]

        pdk = self.config["PDK"]
        scl = self.config["STD_CELL_LIBRARY"]

        tech_info_path = os.path.join(".", "platforms", pdk, scl, "tech.yml")
        tech_info = yaml.safe_load(open(tech_info_path))
        site_info = tech_info.get("site")

        site_width = Decimal(1)
        site_height = Decimal(1)

        if site_info is not None:
            site_width = Decimal(site_info["width"])
            site_height = Decimal(site_info["height"])

            horizontal_halo = math.ceil(horizontal_halo / site_width) * site_width
            vertical_halo = math.ceil(vertical_halo / site_height) * site_height
        else:
            if horizontal_halo != 0.0 or vertical_halo != 0.0:
                warn(
                    "Note: This platform does not have site information. The halo will not be rounded up to the nearest number of sites. This may cause off-by-one issues with some tools."
                )

        die_width = core_width + horizontal_halo * 2
        die_height = core_height + vertical_halo * 2
        if die_height < min_height:
            die_height = min_height
            vertical_halo = (die_height - core_height) / 2
            vertical_halo = math.ceil(vertical_halo / site_height) * site_height

        kwargs, env = self.extract_env(kwargs)

        env["DIE_AREA"] = f"0 0 {die_width} {die_height}"
        env["CORE_AREA"] = (
            f"{horizontal_halo} {vertical_halo} {horizontal_halo + core_width} {vertical_halo + core_height}"
        )
        env["FP_SIZING"] = "absolute"
        return super().run(state_in, env=env, **kwargs)
