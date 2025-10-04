#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright ©2020-2022, The American University in Cairo

import tb_template as RAM_tb
import sys
import re
import math
import os


def dual_ported_test(word_num, word_size, addr_width, model_filename):
    tb = RAM_tb.RAM_instantiation_1RW1R.format(
        word_num=word_num,
        word_size=word_size,
        addr_width=addr_width,
        filename=model_filename,
        pdk_root=os.environ["PDK_ROOT"],
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
