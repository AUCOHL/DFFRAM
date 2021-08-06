import os
import re
import sys
import yaml
from opendb import dbInst as Instance
from typing import List, Dict, Union, TextIO, Optional
from types import SimpleNamespace

from .row import Row
from .util import d2a, DeepDictionary

def dbInst__repr__(self):
    return f"<dbInst {self.getMaster().getName()} {self.getName()}>"

Instance.__repr__ = dbInst__repr__

RegExp = str

class Placeable(object):
    RegexDictionary: Dict[str, Dict[str, RegExp]] = yaml.safe_load(
        open(os.path.join(os.path.dirname(__file__), "rx.yml"))
    )

    def regex_dict(self) -> Dict[str, RegExp]:
        return Placeable.RegexDictionary[self.__class__.__name__]

    class Sieve(object):
        def __init__(self, variable: str, groups: List[str] = [], group_rx_order=None, custom_behavior=None):
            self.variable = variable
            self.groups = groups
            self.groups_rx_order = group_rx_order or list(range(1, len(groups) + 1))
            self.custom_behavior = custom_behavior

    def sieve(self, instances: List[Instance], sieves: List[Sieve]):
        regexes = self.regex_dict()
        compiled_regexes = { k: re.compile(v) for k, v in regexes.items() }
        for sieve in sieves:
            depth = len(sieve.groups)
            if depth == 0:
                self.__dict__[sieve.variable] = None
            else:
                self.__dict__[sieve.variable] = DeepDictionary(depth)
        
        for instance in instances:
            n = instance.getName()
            found = False
            for sieve in sieves:
                rx = compiled_regexes[sieve.variable]
                result = rx.search(n)
                if result is None:
                    continue
                found = True
                if len(sieve.groups_rx_order) == 0:
                    if sieve.custom_behavior is not None:
                        sieve.custom_behavior(instance)
                    else:
                        self.__dict__[sieve.variable] = instance
                else:
                    access_order = []
                    for ordinal in sieve.groups_rx_order:
                        access_order.append(result.group(ordinal))

                    if sieve.custom_behavior is not None:
                        sieve.custom_behavior(instance, *access_order)

                    last_access = access_order.pop()
                    accessible = self.__dict__[sieve.variable]
                    for access in access_order:
                        accessible = accessible[access]
                    
                    accessible[last_access] = instance
                break
            if not found:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

    def place(self, row_list: List[Row], start_row: int = 0) -> int:
        """
        Returns the index of the row after the current one
        """
        raise Exception("Method unimplemented.")

    def represent(self, tab_level: int = -1, file: TextIO = sys.stderr):
        for variable in self.__dict__:
            print(variable, file=file)

    def word_count(self):
        raise Exception("Method unimplemented.")

    def dicts_to_lists(self):
        """
        Transforms all deep dictionaries into sorted lists.
        """
        for key, value in self.__dict__.items():
            if isinstance(value, DeepDictionary):
                self.__dict__[key] = d2a(value, depth=value.depth)

    @staticmethod
    def represent_instance(
        name: str,
        instance: Instance,
        tab_level: int,
        file: TextIO = sys.stderr
    ):
        """
        Writes textual representation of an instance to `file`.
        """
        if name != "":
            name += " "
        print("%s%s%s" % ("".join(["  "] * tab_level), name, instance), file=file)

    ri = represent_instance

    @staticmethod
    def represent_array(
        name: str,
        array: List['Representable'],
        tab_level: int,
        file: TextIO = sys.stderr,
        header: Optional[str] = None
    ):
        """
        Writes textual representation of a list of 'representables' to `file`.

        A representable is an Instance, a Placeable or a list of representables.
        It's a recursive type definition.
        """
        if name != "":
            print("%s%s" % ("".join(["  "] * tab_level), name), file=file)
        tab_level += 1
        for i, instance in enumerate(array):
            if header is not None:
                print("%s%s %i" % ("".join(["  "] * tab_level), header, i), file=file)

            if isinstance(instance, list):
                Placeable.represent_array("", instance, tab_level, file)
            elif isinstance(instance, Placeable):
                instance.represent(tab_level, file)
            else:
                Placeable.represent_instance("", instance, tab_level, file)

        tab_level -= 1

    ra = represent_array

Representable = Union[Instance, 'Placeable',  List['Representable']]

class DataError(Exception):
    pass