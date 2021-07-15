import os
import sys
import yaml
from opendbpy import dbInst as Instance
from typing import List, Dict, Union, TextIO, Optional
from types import SimpleNamespace

from .row import Row
from .util import d2a, DeepDictionary

def dbInst__repr__(self):
    return f"<dbInst {self.getMaster().getName()} {self.getName()}>"

Instance.__repr__ = dbInst__repr__

RegExp = str

RegexDictionary: Dict[str, Dict[str, RegExp]] = yaml.safe_load(
    open(os.path.join(os.path.dirname(__file__), "rx.yml"))
)
def override_regex_dict(override_dict: Dict[str, RegExp]):
    global RegexDictionary
    for key, value in override_dict.items():
        class_name, regex = key.split(".")
        RegexDictionary[class_name][regex] = value

Representable = Union[Instance, 'Placeable',  List['Representable']]

class Placeable(object):
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

    def regexes(self) -> SimpleNamespace:
        """
        Returns a dictionary of regexes for this class accessible with the dot
        notation.
        """
        return SimpleNamespace(**RegexDictionary[self.__class__.__name__])

    def process_dds(self):
        """
        Transforms all deep dictionaries into sorted lists.
        """
        for key, value in self.__dict__.items():
            if isinstance(value, DeepDictionary):
                self.__dict__[key] = d2a(value.vanilla(), depth=value.depth)

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
        array: List[Representable],
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

class DataError(Exception):
    pass