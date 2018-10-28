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