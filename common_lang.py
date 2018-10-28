"""
----------------------------------------------------------------
 Common Language Module.

 Defines storage classes that are shared between VHDL and
 SystemVerilog
----------------------------------------------------------------
"""


class Port:
    """"
    Storage class for ports
    """
    def __init__(self):
        self.name = ""
        self.mode = ""
        self.type = ""
        self.success = False

    def __eq__(self, other):
        return (isinstance(other, Port) and
                self.name == other.name and
                self.mode == other.mode and
                self.type == other.type and
                self.success == other.success)


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
