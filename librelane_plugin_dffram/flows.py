# -*- coding: utf8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright ©2020-2025, The American University in Cairo
# Copyright ©2023 Efabless Corporation
from librelane.flows import SequentialFlow, Flow
from librelane.steps import Yosys, OpenROAD, Magic, KLayout, Netgen, Odb, Checker, Misc

from . import steps as DFFRAM


@Flow.factory.register()
class DFFRAMFlow(SequentialFlow):
    Steps = [
        Yosys.Synthesis,
        Misc.LoadBaseSDC,
        OpenROAD.STAPrePNR,
        DFFRAM.Floorplan,
        DFFRAM.PlaceRAM,
        DFFRAM.Floorplan,
        DFFRAM.PlaceRAM,
        OpenROAD.IOPlacement,
        Odb.CustomIOPlacement,
        OpenROAD.GeneratePDN,
        OpenROAD.STAMidPNR,
        OpenROAD.GlobalRouting,
        OpenROAD.STAMidPNR,
        OpenROAD.DetailedRouting,
        Checker.TrDRC,
        Odb.ReportDisconnectedPins,
        Checker.DisconnectedPins,
        Odb.ReportWireLength,
        Checker.WireLength,
        OpenROAD.RCX,
        OpenROAD.STAPostPNR,
        OpenROAD.IRDropReport,
        Magic.StreamOut,
        Magic.WriteLEF,
        KLayout.StreamOut,
        KLayout.XOR,
        Checker.XOR,
        Magic.DRC,
        Checker.MagicDRC,
        Magic.SpiceExtraction,
        Checker.IllegalOverlap,
        Netgen.LVS,
        Checker.LVS,
    ]
