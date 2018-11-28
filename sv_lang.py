"""
----------------------------------------------------------------
 System Verilog Language Module.

 Defines class structures and methods for identifying and
 manipulating text structures, and extracting and replicating
 lexical elements.
----------------------------------------------------------------
"""
import re
import copy

from . import common_lang
from .vhdl_util import Parentheses, align_block_on_re

_debug = False


# ---------------------------------------------------------------------------
def debug(string):
    """
    Some of these functions ended up with a lot of debug output for analyzing
    processing.  I needed a way to turn it on and off.
    """
    if _debug:
        print(string)


# ---------------------------------------------------------------
class SvPort:
    """
    This is the class of ports and ways to manipulate ports.
    A port consists of a name (string), a mode (optional) (string),
    and a type (string).
    """

    @staticmethod
    def parse_str(port_str: str):
        """Searches a string for the port fields."""
        data = common_lang.Port()

        # Strip any leading / trailing whitespace
        port_str = port_str.strip()

        # In a first step, we look for the (optional) port direction
        dir_pattern = r'(?P<dir>input|output|inout?)\s+'
        s_dir = re.search(re.compile(dir_pattern, re.IGNORECASE), port_str)
        if s_dir:
            data.mode = s_dir.group('dir')

            # remove the port direction and any trailing whitespace
            port_str = re.sub(dir_pattern, '', port_str)
        else:
            data.mode = ''

        # Then we check for unpacked dimensions
        up_pattern = r'(?P<prefix>.*?)\s*(?P<unpacked>\[[^\[]*\])$'
        up_c = re.compile(up_pattern, re.IGNORECASE)

        while True:
            up_s = re.search(up_c, port_str)
            if up_s:
                data.unpacked_dims = up_s.group('unpacked') + data.unpacked_dims
                port_str = up_s.group('prefix')
            else:
                break

        # We try to handle the case with packed dimensions first. In this case there
        # might not be a space between the packed dimensions and the name

        packed_pattern = r'(?P<type>.*?)(\s)*(?P<packed>\[[^\[]*\])(\s)*(?P<name>\S*)$'
        packed_c = re.compile(packed_pattern, re.IGNORECASE)
        packed_s = re.search(packed_c, port_str)

        type_pattern = r'(?P<type>.+?)\s+(?P<name>\S*)$'
        type_s = re.search(re.compile(type_pattern, re.IGNORECASE), port_str)

        if packed_s:
            data.name = packed_s.group('name')
            if packed_s.group('type') != "":
                data.type = packed_s.group('type') + ' ' + packed_s.group('packed')
            else:
                data.type = packed_s.group('packed')
            data.success = True
        elif type_s:
            data.name = type_s.group('name')
            data.type = type_s.group('type')
            data.success = True
        else:
            data.type = ''

            if len(port_str) >= 1:
                data.name = port_str
                data.success = True
            else:
                data.success = False

        if data.success:
            debug('port name: ' + data.name + ", mode: " + data.mode + ", type: " + data.type)
        else:
            print('vhdl-mode: Could not parse port string: ' + port_str + '.')

        return data

    @staticmethod
    def print_as_signal(data: common_lang.Port, name_indicator = ''):
        """Returns a string with the port formatted for a signal."""

        # Trailing semicolon provided by calling routine.
        line = 'wire {} {}{}{}'.format(data.type, name_indicator, data.name, data.unpacked_dims)
        # print(line)
        return line

    @staticmethod
    def print_as_portmap(data: common_lang.Port):
        """Returns a string with the port formatted as a portmap."""
        # A port name might be a comma separated list which
        # needs to be split into several lines.
        # Remove any spaces.
        compact = re.sub(r'\s', '', data.name)
        # Split at commas
        names = compact.split(',')
        lines = []
        for name in names:
            lines.append('.{} ( {} )'.format(name, name))
        # This is a departure from the other "print as" methods as
        # it returns a list instead of a string.
        return lines

    @staticmethod
    def print_as_port(data: common_lang.Port, name_indicator: str = ''):
        """Returns a string with the port formatted as a port."""
        # Trailing semicolon provided by calling routine.
        # The name_indicator is used for alignment in the calling function
        line = '{} {} {}{}{}'.format(data.mode, data.type, name_indicator, data.name, data.unpacked_dims)
        # print(line)
        return line


# ---------------------------------------------------------------
class SvParameter:
    """
    This is the class of parameters and ways to manipulate them.
    A generic consists of a name (string), a type (string),
    and a default value (string).
    """

    @staticmethod
    def parse_str(gen_str: str):
        """Attempts to extract the information from a generic interface."""
        data = common_lang.Generic()

        # Strip any leading / trailing whitespace
        gen_str = gen_str.strip()

        # There a million different options to specify parameters in SV. We
        # only support a reasonable subset of those. For instance information
        # propagation to the following parameters is ignored

        # In a first step, we extract the keyword (ptype) and the default
        # assignment. This is non-optional
        core_pattern = r'(?P<ptype>parameter type|parameter)\s*(?P<core>.*?)\s*=\s*(?P<default>.*?)$'
        core_s = re.search(re.compile(core_pattern, re.IGNORECASE), gen_str)
        if core_s:

            # Store the kind of parameter (value or type)
            if core_s.group('ptype') == 'parameter type':
                data.kind = common_lang.GenericKind.TYPE
            else:
                data.kind = common_lang.GenericKind.VALUE

            # Then store the default assignment
            data.default_value = core_s.group('default')

            # Proceed with the rest of the string
            core_str = core_s.group('core')
        else:
            data.success = False
            return data

        type_pattern = r'^(?P<type>.*)\s+(?P<name>.*?)$'
        type_s = re.search(re.compile(type_pattern, re.IGNORECASE), core_str)

        if type_s:
            data.type = type_s.group('type')
            data.name = type_s.group('name')
            data.success = True
        else:
            data.type = 'int'
            data.name = core_str
            if len(core_str) > 0:
                data.success = True

        if data.success:
            debug("parameter name: " + data.name + ", type: " + data.type + ", assignment: " + data.default_value)
        else:
            print('vhdl-mode: Could not parse generic string: ' + gen_str + '.')

        return data

    @staticmethod
    def print_as_generic(data: common_lang.Generic, name_indicator: str = ''):
        """Returns a string with the generic interface as a generic."""
        if data.kind == common_lang.GenericKind.VALUE:
            line = 'parameter {} {}{} = {}'.format(data.type, name_indicator, data.name, data.default_value)
        elif data.kind == common_lang.GenericKind.TYPE:
            line = 'parameter type {}{} = {}'.format(name_indicator, data.name, data.default_value)
        return line

    @staticmethod
    def print_as_genmap(data: common_lang.Generic):
        """Returns a string with the generic interface as a generic map."""
        line = '.{} ( {} )'.format(data.name, data.name)
        return line

    @staticmethod
    def print_as_constant(data: common_lang.Generic):
        """Returns a string with the generic interface as a constant."""
        # Depends on the kind of parameter
        if data.kind == common_lang.GenericKind.VALUE:
            # In SV a parameter always has a default value
            line = 'const {} {} = {}'.format(data.type, data.name, data.default_value)

        elif data.kind == common_lang.GenericKind.TYPE:
            line = 'typedef {} {}'.format(data.default_value, data.name)

        return line


# ---------------------------------------------------------------
class SVInterface:
    """
    The VhdlInterface class contains the essential elements to a
    VHDL interface structure as defined by an entity or component
    declaration.  In addition, it comprises the methods used to
    extract the structural elements from strings passed to it
    from the Sublime Text API routines, and to produce string
    variations on these structures so that the structure can
    be transformed in various ways.
    """
    def __init__(self):
        self.data = common_lang.Interface()
        self.data.name = ""
        self.data.type = ""
        self.data.if_string = ""
        self.data.if_ports = []
        self.data.if_generics = []

    def name(self):
        return self.data.name

    def interface_start(self, line: str):
        """Attempts to identify the start of an interface."""
        # Checks for module starting lines
        head_pattern = r"(^|\s)(?P<type>module|macromodule)\s*(?P<name>\w*)"
        p = re.compile(head_pattern, re.IGNORECASE)
        s = re.search(p, line)
        # debug(line)
        if s:
            # Note, it's returning the horizontal position which
            # is different from the "startpoint" class variable
            # above which is the position in the file.
            self.data.type = s.group('type')
            self.data.name = s.group('name')
            debug("Hit at: " + line)
            debug("type: " + self.data.type + ", name: " + self.data.name)
            return s.start()
        else:
            return None

    def interface_end(self, line: str):
        """Attempts to identify the end of an interface."""
        # Checks to see if the line passed contains the
        # end string matching the starting type.  The
        # type and name are optional technically.
        tail_pattern = r"endmodule".format(self.data.type, self.data.name)
        p = re.compile(tail_pattern, re.IGNORECASE)
        s = re.search(p, line)
        if s:
            # The end point (from experimentation) seems to
            # be the index AFTER the final character, so
            # subtracting 1 here for the return value.
            debug("End hit at " + line)
            return s.end()
        else:
            return None

    @staticmethod
    def strip_comments(if_string: str):
        """Removes comments from the interface to aid parsing."""
        # Comments will likely screw up the parsing of the
        # block and we don't need to copy them, so strip them out
        # TODO : Handle block comments someday.
        p = re.compile(r"(?://).*?(\n|$)")
        if_string = re.sub(p, r"\n", if_string)
        return if_string

    @staticmethod
    def strip_whitespace(if_string: str):
        """Removes extra whitespace to aid parsing."""
        # Making sure I don't have to deal with newlines while
        # parsing.  Changing all whitespace to a single space.
        # This is required due to rules regarding port modes
        # which might conflict with type names.
        p = re.compile(r"\s+")
        if_string = re.sub(p, " ", if_string)
        return if_string

    def parse_parameter_port(self, if_string: str):
        """Attempts to break the interface into known parameter and
        port sections and then calls individual parsing routines."""
        # Initialize things.
        self.data.if_ports = []
        self.data.if_generics = []

        # Now checking for the existence of generic and port zones.
        # Split into generic string and port strings and then parse
        # each separately.  Standard demands generic first, then port.
        parameter_pattern = re.compile(r'#\s*\((.*?)\)', re.I)
        port_pattern = re.compile(r'\((.*?)\)', re.I)

        parameter_search = re.search(parameter_pattern, if_string)

        # The parameter declarations comes first
        if parameter_search:
            parameter_str = Parentheses().extract(if_string[parameter_search.start():])
            # debug("Par str: " + parameter_str)

            # remove the parameters from the string
            if_string = re.sub(parameter_pattern, "", if_string)
            # debug("New if str: " + if_string)

        # Now that all the parameters have been removed, we can look for the ports
        port_search = re.search(port_pattern, if_string)

        if port_search:
            port_str = Parentheses().extract(if_string[port_search.start():])
            body_str = re.sub(port_pattern, '', if_string, count=1)
            # debug("VhdlPort str: " + port_str)
        else:
            body_str = if_string

        # Now parse the two strings and make them into lists

        # Parse the parameter string
        if parameter_search and parameter_str is not None:
            parameter_list = parameter_str.split(',')
            for item in parameter_list:
                parameter = SvParameter.parse_str(item)
                if parameter.success:
                    self.data.if_generics.append(parameter)
        else:
            print('vhdl-mode: No parameters found.')

        # Parse the port string
        if port_search and port_str is not None:
            port_list = port_str.split(',')
            for item in port_list:
                port = SvPort.parse_str(item)
                if port.success:
                    self.data.if_ports.append(port)
        else:
            print('vhdl-mode: No ports found.')

        # Now we have to parse the body of the module to
        # find additional definitions
        body_pattern = r'(?P<dir>input|output|inout?)\s+'
        body_c = re.compile(body_pattern, re.IGNORECASE)

        body_list = body_str.split(';')
        for body_line in body_list:
            if body_c.search(body_line):
                port = SvPort.parse_str(body_line)

                # Replace the existing port in the port list with
                # the new port
                hit = False
                for i in range(0, len(self.data.if_ports)):
                    if port.name == self.data.if_ports[i].name:
                        hit = True
                        self.data.if_ports[i] = port
                        break

                if not hit:
                    print('vhdl-mode: Could not find a port named ' + port.name + ' in the port header.')




    def parse_block(self, if_string: str):
        """Top level routine for extracting information out of a
        string block believed to contain a VHDL interface."""
        # This contains the whole parsing routine in a single method
        # because the calling command method doesn't need to know
        # about it.
        if_string = self.strip_comments(if_string)
        if_string = self.strip_whitespace(if_string)
        self.parse_parameter_port(if_string)

        return self.data

    def signals(data):
        """
        This method returns a string that consists of the interface
        listed as signals
        """
        lines = []
        # Construct structure and insert
        if data.data.if_ports:
            for port in data.data.if_ports:
                lines.append(SvPort.print_as_signal(port, name_indicator=',') + ';')

            # Use the indicator to align the names, and then remove it
            align_block_on_re(lines, r',', lang='sv')
            lines = [re.sub(r',', '', i) for i in lines]

            indent_sv(lines, 1)
            return '\n'.join(lines)
        else:
            return None

    def constants(self):
        """
        This method returns the generic portion of the interface
        listed as constants.
        """
        lines = []
        if self.data.if_generics:
            for generic in self.data.if_generics:
                lines.append(SvParameter.print_as_constant(generic) + ';')
            align_block_on_re(lines, r'=', lang='sv')
            indent_sv(lines, 1)
            return '\n'.join(lines)
        else:
            return None

    def instance(self, instances={}, name=""):
        """This method returns a string that consists of the
        interface listed as an instantiation
        """
        # Choose a name based on a given (for testbench use) or
        # regular instantiation.
        if name:
            inst_name = name
        elif self.data.name in instances:
            instance_count = len(instances[self.data.name])
            inst_name = self.data.name+'_{}'.format(instance_count+1)
            # Check for duplicate name and just increment index until clear.
            while inst_name in instances[self.data.name]:
                instance_count += 1
                inst_name = self.data.name+'_{}'.format(instance_count+1)
        else:
            inst_name = self.data.name+'_1'
        lines = []
        lines.append("{}".format(self.data.name))
        if self.data.if_generics:
            lines[-1] += " #("
            # Put the generics in here.  Join with , and a temp
            # character then split at the temp character.  That
            # should create the lines with commas on all but
            # the last.
            gen_strings = []
            for generic in self.data.if_generics:
                gen_strings.append(SvParameter.print_as_genmap(generic))
            gen_strings = ',^'.join(gen_strings).split('^')

            align_block_on_re(gen_strings, r'.', lang='sv')
            align_block_on_re(gen_strings, r'\(', lang='sv')
            align_block_on_re(gen_strings, r'\)', lang='sv')

            for gen_str in gen_strings:
                lines.append(gen_str)
            lines.append(")")
        lines[-1] += " {}".format(inst_name)
        if self.data.if_ports:
            lines[-1] += " ("
            # Put the ports in here.  Same as before.
            port_strings = []
            for port in self.data.if_ports:
                # Print as portmap returns a list unlike others
                for mapping in SvPort.print_as_portmap(port):
                    port_strings.append(mapping)
            port_strings = ',^'.join(port_strings).split('^')

            align_block_on_re(port_strings, r'.', lang='sv')
            align_block_on_re(port_strings, r'\(', lang='sv')
            align_block_on_re(port_strings, r'\)', lang='sv')

            for port_str in port_strings:
                lines.append(port_str)
            lines.append(")")
        lines[-1] += ";"

        indent_sv(lines, 1)

        return '\n'.join(lines)

    def entity(self):
        """
        Returns a string with the interface written as an
        entity declaration.
        """
        # Construct structure
        lines = []
        lines.append("module {}".format(self.data.name))
        if self.data.if_generics:
            lines[-1] += ' #('
            # Put the generics in here.  Join with ; and a temp
            # character then split at the temp character.  That
            # should create the lines with semicolons on all but
            # the last.
            gen_strings = []
            for generic in self.data.if_generics:
                gen_strings.append(SvParameter.print_as_generic(generic, name_indicator=','))

            # Align the lines
            # Use the indicator to align the names, and then remove it
            align_block_on_re(gen_strings, r',', lang='sv')
            gen_strings = [re.sub(r',', '', i) for i in gen_strings]
            align_block_on_re(gen_strings, r'=', lang='sv')

            gen_strings = ',^'.join(gen_strings).split('^')
            for gen_str in gen_strings:
                lines.append(gen_str)
            lines.append(")")
        if self.data.if_ports:
            lines[-1] += ' ('
            # Put the ports in here.  Same as before.
            port_strings = []
            for port in self.data.if_ports:
                port_strings.append(SvPort.print_as_port(port, name_indicator=','))

            # Align the lines
            align_block_on_re(port_strings, r'^\s?(input\b|output\b|inout\b)?\s*', padside='post', lang='sv')
            # Use the indicator to align the names, and then remove it
            align_block_on_re(port_strings, r',', lang='sv')
            port_strings = [re.sub(r',', '', i) for i in port_strings]

            port_strings = ',^'.join(port_strings).split('^')
            for port_str in port_strings:
                lines.append(port_str)
            lines.append(")")
        lines[-1] += ";"
        lines.append("endmodule // {}".format(self.data.name))

        indent_sv(lines, 0)

        return '\n'.join(lines)

    def flatten(self):
        """
        Iterates over the generics and ports and if there
        is a line with multiple token names on the same line, will
        make copies of that port with the individual token names.
        """
        if self.data.if_generics:
            new_generics = []
            for generic in self.data.if_generics:
                if ',' in generic.name:
                    name_list = re.sub(r'\s*,\s*', ',', generic.name).split(',')
                    for name in name_list:
                        new_generic = copy.copy(generic)
                        new_generic.name = name
                        new_generics.append(new_generic)
                else:
                    new_generics.append(generic)
            self.data.if_generics = new_generics
        if self.data.if_ports:
            new_ports = []
            for port in self.data.if_ports:
                if ',' in port.name:
                    name_list = re.sub(r'\s*,\s*', ',', port.name).split(',')
                    for name in name_list:
                        new_port = copy.copy(port)
                        new_port.name = name
                        new_ports.append(new_port)
                else:
                    new_ports.append(port)
            self.data.if_ports = new_ports

    def reverse(self):
        """
        Iterates over the ports and flips the direction/mode.
        in becomes out
        out and buffer become in
        inout is unchanged.
        """
        if self.data.if_ports:
            for port in self.data.if_ports:
                if port.mode.lower() == 'input':
                    port.mode = 'output'
                elif port.mode.lower() == 'output':
                    port.mode = 'input'


# ---------------------------------------------------------------
def indent_sv(lines, initial=0, tab_size=4, use_spaces=False):
    """
    Implements SV indenting based on brackets only
    """

    # Set the indent to tabs or spaces here
    if use_spaces:
        indent_char = ' '*tab_size
    else:
        indent_char = '\t'

    current_indent = initial
    for i in range(0, len(lines)):
        line = lines[i]

        min_indent = current_indent
        for j in range(0, len(line)):
            if line[j] == '(':
                current_indent += 1
            elif line[j] == ')':
                current_indent -= 1
                min_indent = min(current_indent, min_indent)

        # Modify the line here.
        lines[i] = indent_char * min_indent + line

