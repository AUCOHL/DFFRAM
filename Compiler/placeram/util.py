import sys

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def d2a(d):
    as_list = list(d.items())
    as_list.sort(key=lambda x: x[0])
    return list(map(lambda x: x[1], as_list))