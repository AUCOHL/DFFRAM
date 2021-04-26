import tb_template as RAM_tb
import tb_template_1RW1R as RAM_1RW1R_tb
import sys
import re
import math

if __name__ == "__main__":
    PATTERN = sys.argv[1]
    word_num = int(re.search('RAM(\d+)x', PATTERN).group(1))
    if "1RW1R" in PATTERN:
        word_size = int(re.search(r"x(\d+)_", PATTERN).group(1))
        themodule = RAM_1RW1R_tb
        filename = 'tb_RAM{word_num}x{word_size}_1RW1R.v'.format(word_num=word_num,
        word_size=word_size)
    else:
        word_size = int(re.search(r"x(\d+)$", PATTERN).group(1))
        themodule = RAM_tb
        filename = 'tb_RAM{word_num}x{word_size}.v'.format(word_num=word_num,
        word_size=word_size)

    addr_width = int(math.log2(word_num))
    tb = themodule.changeable_sub.format(word_num=word_num,
            word_size=word_size, addr_width=addr_width)
    tb += themodule.constant_sub
    with open(filename, 'w+') as f:
        f.write(tb)
