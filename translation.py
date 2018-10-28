"""
----------------------------------------------------------------
 Translation Module.

 Defines functions to translate between VHDL and
 (System) Verilog. Note that this implements only a subset
 of the languages, which would be used at an interface.
----------------------------------------------------------------
"""

from .common_lang import Generic, Interface, Port
import re


class Translation:

    @staticmethod
    def interface_vhdl_to_sv(if_vhdl: Interface):
        return if_vhdl

    @staticmethod
    def interface_sv_to_vhdl(if_sv: Interface):
        return if_sv

    @staticmethod
    def generic_sv_to_vhdl(gen_sv: Generic):
        return gen_sv

    @staticmethod
    def generic_vhdl_to_sv(gen_vhdl: Generic):
        return gen_vhdl

    @staticmethod
    def port_sv_to_vhdl(port_sv: Port):
        return port_sv

    @staticmethod
    def port_vhdl_to_sv(port_vhdl: Port):
        return port_vhdl

    @staticmethod
    def mode_sv_to_vhdl(mode_sv: str):
        """"Translates the mode (direction) of a port from SV to VHDL"""

        mode_table = {
            'input': 'in',
            'output': 'out',
            'inout': 'inout',
        }

        mode_vhdl = mode_table.get(mode_sv)
        if mode_vhdl is None:
            print('vhdl-mode: Could not convert port mode: ' + mode_sv)
            mode_vhdl = 'ERR'
        return mode_vhdl

    @staticmethod
    def mode_vhdl_to_sv(mode_vhdl: str):
        """"Translates the mode (direction) of a port from VHDL to SV"""

        mode_table = {
            'in': 'input',
            'out': 'output',
            'inout': 'inout',
        }

        mode_sv = mode_table.get(mode_vhdl)
        if mode_sv is None:
            print('vhdl-mode: Could not convert port mode: ' + mode_vhdl)
            mode_sv = 'ERR'

        return mode_sv

    @staticmethod
    def type_sv_to_vhdl(type_sv: str):
        """"Translates the type of a port/generic from SV to VHDL"""
        pattern_vec = r'(?P<type>.*?)\s+\[(?P<upper>\d+):(?P<lower>\d+)\]'
        search_vec = re.search(re.compile(pattern_vec, re.IGNORECASE), type_sv)

        if search_vec:
            # vector with a packed dimension
            type_sv = search_vec.group('type')
            trailer_vhdl = '_vector(' + search_vec.group('upper') + \
                           ' downto ' + search_vec.group('lower') + ')'
        else:
            # just a scalar
            trailer_vhdl = ''

        type_table = {
            'reg': 'std_logic',
            'bit': 'std_logic',
            'logic': 'std_logic',
            'integer': 'integer',
            'int': 'integer',
        }

        type_vhdl = type_table.get(type_sv)
        if type_vhdl is None:
            type_vhdl = "ERR"
            print('vhdl-mode: Could not convert type ' + type_sv)

        return type_vhdl + trailer_vhdl

    @staticmethod
    def type_vhdl_to_sv(type_vhdl: str):
        """"Translates the type of a port/generic from VHDL to SV"""
        pattern_vec = r'(?P<type>.*?)_vector\s*\((?P<upper>\d+)\s+downto\s+(?P<lower>\d+)\)'
        search_vec = re.search(re.compile(pattern_vec, re.IGNORECASE), type_vhdl)

        if search_vec:
            # vector with a packed dimension
            type_vhdl = search_vec.group('type')
            trailer_sv = ' [' + search_vec.group('upper') + \
                         ':' + search_vec.group('lower') + ']'
        else:
            # just a scalar
            trailer_sv = ''

        type_table = {
            'std_logic': 'logic',
            'std_ulogic': 'logic',
            'bit': 'logic',
            'integer': 'integer',
            'natural': 'integer',
            'positive': 'integer',
        }

        type_sv = type_table.get(type_vhdl)
        if type_sv is None:
            type_sv = "ERR"
            print('vhdl-mode: Could not convert type ' + type_vhdl)

        return type_sv + trailer_sv
