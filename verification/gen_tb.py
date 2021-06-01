#!/usr/bin/env python3
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

import tb_template as RAM_tb
import sys
import re
import math
import os
def dual_ported_test(word_num, word_size, addr_width, model_filename):
    tb = RAM_tb.RAM_instantiation_1RW1R.format(word_num=word_num,
            word_size=word_size,
            addr_width=addr_width,
            filename=model_filename,
            pdk_root=os.environ["PDK_ROOT"])

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
    tb = RAM_tb.RAM_instantiation.format(word_num=word_num,
            word_size=word_size,
            addr_width=addr_width,
            filename=model_filename,
            pdk_root=os.environ["PDK_ROOT"])
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
    word_num = int(re.search('RAM(\d+)x', PATTERN).group(1))
    addr_width = int(math.log2(word_num))
    model_filename = os.path.realpath("../platforms/sky130A/BB/ram/model.v")
    if "1RW1R" in PATTERN:
        word_size = int(re.search(r"x(\d+)_", PATTERN).group(1))
        filename = 'tb_RAM{word_num}x{word_size}_1RW1R.v'.format(word_num=word_num,
        word_size=word_size)
        module = "RAM{word_num}_1RW1R".format(word_num=word_num)
        tb = dual_ported_test(word_num, word_size, addr_width, model_filename)
    else:
        word_size = int(re.search(r"x(\d+)$", PATTERN).group(1))
        filename = 'tb_RAM{word_num}x{word_size}.v'.format(word_num=word_num,
        word_size=word_size)
        module = "RAM{word_num}".format(word_num=word_num)
        tb = single_ported_test(word_num, word_size, addr_width, model_filename)


    with open(filename, 'w+') as f:
        f.write(tb)
    print(module)
