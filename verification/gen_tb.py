#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright ©2020-2022, The American University in Cairo

import tb_template as RAM_tb
import sys
import re
import math
import os

# The platform's cell models the testbench includes (from the platform's
# directory, which the Makefile puts on the include path): a standard cell
# library whose Verilog comes in one file is just "<SCL>.v"; gf180mcu's
# needs its UDP primitives first.
CELL_MODELS = {
    "sky130_fd_sc_hd": ["sky130_fd_sc_hd.v"],
    "gf180mcu_fd_sc_mcu7t5v0": ["primitives.v", "gf180mcu_fd_sc_mcu7t5v0.v"],
}


def cell_model_includes():
    # The block definitions switch implicit nets off (`default_nettype none)
    # and a vendor's cell models may rely on them (gf180mcu's do), so they
    # are included with implicit nets on and the strict setting restored.
    scl = os.getenv("SCL") or "sky130_fd_sc_hd"
    files = CELL_MODELS.get(scl, [f"{scl}.v"])
    lines = ["`default_nettype wire"]
    lines += [f'`include "{f}"' for f in files]
    lines += ["`default_nettype none"]
    return "\n".join(lines)


def dual_ported_test(word_num, word_size, addr_width, model_filename):
    tb = RAM_tb.RAM_instantiation_1RW1R.format(
        word_num=word_num,
        word_size=word_size,
        addr_width=addr_width,
        filename=model_filename,
        pdk_root=os.environ["PDK_ROOT"],
        cell_models=cell_model_includes(),
    )

    tb += RAM_tb.start_test_common
    tb += RAM_tb.begin_dual_ported_test
    tb += RAM_tb.dual_ported_custom_test
    tb += RAM_tb.test_port_1RW1R
    tb += RAM_tb.test_port_RW
    tb += RAM_tb.end_test
    tb += RAM_tb.tasks
    tb += RAM_tb.dual_ported_tasks
    tb += RAM_tb.endmodule

    return tb


def single_ported_test(word_num, word_size, addr_width, model_filename):
    tb = RAM_tb.RAM_instantiation.format(
        word_num=word_num,
        word_size=word_size,
        addr_width=addr_width,
        filename=model_filename,
        pdk_root=os.getenv("PDK_ROOT") or "/",
        cell_models=cell_model_includes(),
    )
    tb += RAM_tb.start_test_common
    tb += RAM_tb.begin_single_ported_test
    tb += RAM_tb.single_ported_custom_test
    tb += RAM_tb.test_port_RW
    tb += RAM_tb.end_test
    tb += RAM_tb.tasks
    tb += RAM_tb.endmodule

    return tb


if __name__ == "__main__":
    PATTERN = sys.argv[1]
    word_num = int(re.search(r"RAM(\d+)x", PATTERN).group(1))
    addr_width = int(math.log2(word_num))
    model_filename = os.path.realpath("../models/ram/model.v")
    if "1RW1R" in PATTERN:
        word_size = int(re.search(r"x(\d+)_", PATTERN).group(1))
        filename = f"tb_RAM{word_num}x{word_size}_1RW1R.v"
        module = f"RAM{word_num}_1RW1R"
        tb = dual_ported_test(word_num, word_size, addr_width, model_filename)
    else:
        word_size = int(re.search(r"x(\d+)$", PATTERN).group(1))
        filename = f"tb_RAM{word_num}x{word_size}.v"
        module = f"RAM{word_num}"
        tb = single_ported_test(word_num, word_size, addr_width, model_filename)

    with open(filename, "w+") as f:
        f.write(tb)
    print(module)
