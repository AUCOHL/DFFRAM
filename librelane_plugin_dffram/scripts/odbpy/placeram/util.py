# -*- coding: utf8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright ©2020-2022, The American University in Cairo

import sys
import collections
from typing import Dict, List, TypeVar

T = TypeVar("T")


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def d2a(d: Dict[int, T], depth=1) -> List:
    """
    Dictionary To Array
    >>> d2a({ 2: "and", 1: "potatoes", 0: "mashed", 3: "gravy"})
    ['mashed', 'potatoes', 'and', 'gravy']
    >>> d2a({ 1: { 1: "lamb", 0: "little"}, 0: {4: "lamb", 1: "had", 2: "a", 3: "little", 0: "mary"}}, depth=1)
    [{4: 'lamb', 1: 'had', 2: 'a', 3: 'little', 0: 'mary'}, {1: 'lamb', 0: 'little'}]
    >>> d2a({ 1: { 1: "lamb", 0: "little"}, 0: {4: "lamb", 1: "had", 2: "a", 3: "little", 0: "mary"}}, depth=2)
    [['mary', 'had', 'a', 'little', 'lamb'], ['little', 'lamb']]
    """
    as_list = list(d.items())
    if depth > 1:
        for i, (key, value) in enumerate(as_list):
            as_list[i] = (key, d2a(value, depth=depth - 1))

    as_list.sort(key=lambda x: x[0])
    return list(map(lambda x: x[1], as_list))


class DeepDictionary(collections.abc.MutableMapping):
    def __init__(self, depth=1, *args, **kwargs):
        if depth < 1:
            raise ValueError(
                "cannot initialize deep dictionary of a depth less than one"
            )
        self.depth = depth
        self.store = dict()
        self.update(dict(*args, **kwargs))

    def __getitem__(self, key):
        get_result = self.store.get(key)
        if get_result is None:
            if (self.depth - 1) < 1:
                raise KeyError("access exceeded depth of deep dictionary")
            self.store[key] = DeepDictionary(depth=self.depth - 1)
        return self.store[key]

    def __setitem__(self, key, value):
        self.store[key] = value

    def __delitem__(self, key):
        del self.store[key]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __repr__(self):
        return str(self.store)

    def vanilla(self, depth=None):
        if depth is None:
            depth = self.depth
        vanilla_dict = {}
        for key, value in self.store.items():
            if isinstance(value, DeepDictionary):
                vanilla_dict[key] = value.vanilla(depth - 1)
            else:
                vanilla_dict[key] = value

        return vanilla_dict
