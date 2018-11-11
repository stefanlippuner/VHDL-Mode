"""
----------------------------------------------------------------
 Common Language Module.

 Defines storage classes that are shared between VHDL and
 SystemVerilog
----------------------------------------------------------------
"""
from copy import deepcopy


class Port:
    """"
    Storage class for ports
    """
    def __init__(self):
        self.name = ""
        self.mode = ""
        self.type = ""
        self.unpacked_dims = ""
        self.success = False

    def __eq__(self, other):
        return (isinstance(other, Port) and
                self.name == other.name and
                self.mode == other.mode and
                self.type == other.type and
                self.unpacked_dims == other.unpacked_dims and
                self.success == other.success)

    def __deepcopy__(self, memodict={}):
        newone = type(self)()
        newone.name = self.name
        newone.mode = self.mode
        newone.type = self.type
        newone.unpacked_dims = self.unpacked_dims
        newone.success = self.success
        return newone


class GenericKind:
    VALUE = 0
    TYPE = 1


class Generic:
    """"
    Storage class for generics / parameters
    """
    def __init__(self):
        self.name = ""
        self.type = ""
        self.kind = GenericKind.VALUE
        self.default_value = ""
        self.success = False

    def __eq__(self, other):
        return (isinstance(other, Generic) and
                self.name == other.name and
                self.type == other.type and
                self.kind == other.kind and
                self.default_value == other.default_value and
                self.success == other.success)

    def __deepcopy__(self, memodict={}):
        newone = type(self)()
        newone.name = self.name
        newone.type = self.type
        newone.kind = self.kind
        newone.default_value = self.default_value
        newone.success = self.success
        return newone


class Interface:
    """
    Storage class for an entire interface (component / instantiation / ...)
    """
    def __init__(self):
        self.name = ""
        self.type = ""
        self.if_string = ""
        self.if_ports = []
        self.if_generics = []

    def __eq__(self, other):
        return (isinstance(other, Interface) and
                self.name == other.name and
                self.type == other.type and
                self.if_ports == other.if_ports and
                self.if_generics == other.if_generics)

    def __deepcopy__(self, memodict={}):
        newone = type(self)()
        newone.name = self.name
        newone.type = self.type
        newone.if_string = self.if_string
        newone.if_ports = deepcopy(self.if_ports, memodict)
        newone.if_generics = deepcopy(self.if_generics,memodict)
        return newone
