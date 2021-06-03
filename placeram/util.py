# -*- coding: utf8 -*-
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

import sys
from types import SimpleNamespace
from typing import Any, Dict, List, T

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def d2a(d: Dict[int, T]) -> List[T]:
    """
    Dictionary To Array
    >>> d2a({ 2: "and", 1: "potatoes", 0: "mashed", 3: "gravy"})
    ['mashed', 'potatoes', 'and', 'gravy']
    """
    as_list = list(d.items())
    as_list.sort(key=lambda x: x[0])
    return list(map(lambda x: x[1], as_list))

def sarv(obj: SimpleNamespace, name: str, expr: T) -> T:
    """
    Set Attribute And Return Value

    A workaround for := not being available below Python 3.8.
    """
    setattr(obj, name, expr)
    return expr
