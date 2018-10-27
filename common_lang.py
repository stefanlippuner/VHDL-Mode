"""
----------------------------------------------------------------
 Common Language Module.

 Defines storage classes that are shared between VHDL and
 SystemVerilog
----------------------------------------------------------------
"""

class Port:

    def __init__(self):
        self.name = ""
        self.mode = ""
        self.type = ""
        self.success = False
