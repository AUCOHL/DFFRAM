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
import tb_template_1RW1R as RAM_1RW1R_tb
import sys
import re
import math
import os

if __name__ == "__main__":
    PATTERN = sys.argv[1]
    word_num = int(re.search('RAM(\d+)x', PATTERN).group(1))
    if "1RW1R" in PATTERN:
        model_filename = os.path.realpath("../sky130A/BB/experimental/model.v")
        word_size = int(re.search(r"x(\d+)_", PATTERN).group(1))
        themodule = RAM_1RW1R_tb
        filename = 'tb_RAM{word_num}x{word_size}_1RW1R.v'.format(word_num=word_num,
        word_size=word_size)
    else:
        word_size = int(re.search(r"x(\d+)$", PATTERN).group(1))
        themodule = RAM_1RW1R_tb
        filename = 'tb_RAM{word_num}x{word_size}.v'.format(word_num=word_num,
        word_size=word_size)

    addr_width = int(math.log2(word_num))
    tb = themodule.changeable_sub.format(word_num=word_num,
            word_size=word_size, addr_width=addr_width, filename=model_filename)
    tb += themodule.constant_sub
    with open(filename, 'w+') as f:
        f.write(tb)
