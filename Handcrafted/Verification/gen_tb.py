import tb_template
import sys
import re
import math

if __name__ == "__main__":
    PATTERN = sys.argv[1]
    word_num = int(re.search('tb_RAM(.*)x32', PATTERN).group(1))
    address_lines_num = int(math.log2(word_num))
    tb = tb_template.changeable_sub.format(word_num,
            address_lines_num)
    tb += tb_template.constant_sub
    with open('tb_RAM{}x32_gen.v'.format(word_num), 'w+') as f:
        f.write(tb)
