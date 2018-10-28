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

_debug = True


# ---------------------------------------------------------------------------
def debug(string):
    """
    Some of these functions ended up with a lot of debug output for analyzing
    processing.  I needed a way to turn it on and off.
    """
    if _debug:
        print(string)


# ---------------------------------------------------------------
class Parentheses:
    """
    An object whose purpose is to keep track of parenthesis counts
    and provide helper functions while traversing a text file.

    May be initialized with a two element list indicating the starting
    counts if needed.

    open_cnt and close_cnt represent the current number of unmatched
    open and closing parentheses.

    open_pos and close_pos represent the character position of the UNMATCHED
    open and closing parentheses in the last scanned string.
    """
    def __init__(self, counts=[0, 0]):
        self.open_cnt = counts[0]
        self.close_cnt = counts[1]
        self.open_pos = []
        self.close_pos = []

    @property
    def delta(self):
        return self.open_cnt - self.close_cnt

    @property
    def balanced(self):
        return bool(self.open_cnt == self.close_cnt)

    def reset(self):
        self.__init__()

    def scan(self, line):
        # Reset the position lists.
        self.open_pos = []
        self.close_pos = []
        for i in range(len(line)):
            if line[i] == '(':
                # If we find a ( then increment the count and append the
                # position.
                self.open_cnt += 1
                self.open_pos.append(i)
            elif line[i] == ')':
                # If we find a ) there are several options.
                # If open_pos has members, pop off the mate.  Also decrement
                # the count.
                # If open_cnt > 0 then decrement the count of the prior
                # unmatched open.
                # If open_cnt = 0 then increment the closing count and
                # append the position.
                if self.open_pos:
                    self.open_cnt -= 1
                    self.open_pos.pop()
                elif self.open_cnt > 0:
                    self.open_cnt -= 1
                else:
                    self.close_pos.append(i)
                    self.close_cnt += 1

    def stats(self):
        return '#(={}, #)={}, OPos={}, CPos={}'.format(self.open_cnt,
            self.close_cnt, self.open_pos, self.close_pos)

    def extract(self, line):
        """Given a string, extracts the contents of the next parenthetical
        grouping (including interior parenthetical groups.)"""
        start = 0
        end = 0
        pcount = 0
        for i in range(len(line)):
            if line[i] == '(' and pcount == 0:
                pcount += 1
                start = i + 1
            elif line[i] == '(':
                pcount += 1

            if line[i] == ')' and pcount > 1:
                pcount -= 1
            elif line[i] == ')' and pcount == 1:
                end = i
                pcount -= 1
                break
        if start >= end:
            return None
        else:
            return line[start:end]

# ---------------------------------------------------------------
def align_block_on_re(lines, regexp, padside='pre', ignore_comment_lines=True, scope_data=None):
    """
    Receives a list of individual lines.  Scans each line looking
    for the provided lexical pattern that should align on
    adjoining lines. Once a pattern is found, record the line index
    and pattern location.  For each subsequent line that also
    identifies the pattern, add the line index and pattern location.
    When a line is identified that does not have the pattern, find
    the line in the list with the most leftmost symbol, and then
    iterate through the list of affected lines and pad on the side
    declared (anything that is not 'post' is prepend because that's
    most common.)

    Alignment should happen when the strings are left justified
    so that it doesn't need to know about the spacing.

    This is intended to be run in several passes on several patterns
    which is why it takes the regexp as a parameter.

    Added some blacklist words, otherwise you can get some matching
    between conditionals and assignments and other nonsense.

    TODO: Add scope checking for alignment instead of ban list
    when provided.
    """
    ban_raw = [
        r':\s+process\b',
        r'\bif\b',
        r'\bthen\b',
        r'\bwhen\b(?=.*?=>)'
    ]
    ban_list = []
    for pattern in ban_raw:
        ban_list.append(re.compile(pattern, re.IGNORECASE))

    prior_scope = ""
    match_data = []
    for i in range(len(lines)):

        # Check for banned lines we don't even want to think about.
        banned = False
        for pattern in ban_list:
            ban_search = re.search(pattern, lines[i])
            if ban_search:
                banned = True
                break

        # Adding a hook here for better comment handling.  Check to see if this
        # is a commented line and if we should pay attention to it.
        # ignore_comment_lines is True by default and until this routine is
        # more sophisticated should probably remain true.
        comment_check = False
        if ignore_comment_lines:
            comment_check = check_for_comment(lines[i])

        # Scan for the aligning pattern
        s = re.search(regexp, lines[i])

        # First decide if based on lack of pattern, scope change, or
        # a banned line or end of file whether we should process any
        # currently existing match list.
        scope_switch = False
        if scope_data is not None:
            if scope_data[i] != prior_scope:
                scope_switch = True
            else:
                scope_switch = False

        # A special check for the last line to add to the group, otherwise
        # we process before we can evaluate that line.
        if s and (i == len(lines)-1) and not comment_check and not banned:
            if padside == 'post':
                match_data.append((i, s.end()))
            else:
                match_data.append((i, s.start()))

        # This is where the actual lines are adjusted.  If this line breaks the
        # sequence of lines that had the pattern, or if it's the last line, or
        # if it was a line that was skipped due to banning, or if the whole
        # line scope changed (e.g. comment line broke the block) then process
        # the block for alignment.
        if not s or scope_switch or (i == len(lines)-1) or banned:
            if len(match_data) > 1:
                # Scan for max value and check to see if extra space needed
                # due to lack of preceding space.
                maxpos = 0
                for pair in match_data:
                    if pair[1] > maxpos:
                        maxpos = pair[1]
                        if lines[pair[0]][pair[1]-1] != ' ':
                            maxpos = maxpos + 1
                # Now insert spaces on each line (max-current+1)
                # to make up the space.
                for pair in match_data:
                    lines[pair[0]] = lines[pair[0]][0:pair[1]] + \
                                     ' '*(maxpos-pair[1]) + \
                                     lines[pair[0]][pair[1]:]
            # No match for more than one line so erase match
            # data
            match_data = []

        # Finally, if this line has an alignment symbol in it (and not banned)
        # start adding data again.
        if s and not comment_check and not banned:
            # If we find a match, record the line and
            # location but do nothing else.
            #print("Match on Line: {} Start:'{}' Stop:'{}'".\
            #       format(line_num, lines[line_num][0:s.start()],\
            #              lines[line_num][s.start():]))
            if padside == 'post':
                match_data.append((i, s.end()))
            else:
                match_data.append((i, s.start()))

        # Make sure we save the current scope off before looping
        if scope_data is not None:
            prior_scope = scope_data[i]


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

        # In a first step, we look for the (optional) port direction
        dir_pattern = r'(?P<dir>input|output|inout?)\s+'
        s_dir = re.search(re.compile(dir_pattern, re.IGNORECASE), port_str)
        if s_dir:
            data.mode = s_dir.group('dir')

            # remove the port direction and any trailing whitespace
            port_str = re.sub(dir_pattern, '', port_str)
        else:
            data.mode = 'inout'

        type_pattern = r'(?P<type>.*?)\s+(?P<name>\S*)$'
        pp = re.compile(type_pattern, re.IGNORECASE)
        s = re.search(pp, port_str)

        if s:
            data.name = s.group('name')
            data.type = s.group('type')
            data.success = True
        else:
            data.type = 'wire'

            if len(port_str) >= 1:
                data.name = port_str
                data.success = True
            else:
                data.success = False

        if data.success:
            print('port name: ' + data.name + ", mode: " + data.mode + ", type: " + data.type)
        else:
            print('vhdl-mode: Could not parse port string: ' + port_str + '.')

        return data

    @staticmethod
    def print_as_signal(data: common_lang.Port):
        """Returns a string with the port formatted for a signal."""
        # Trailing semicolon provided by calling routine.
        line = 'signal {} : {}'.format(data.name, data.type)
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
            lines.append('{} => {}'.format(name, name))
        # This is a departure from the other "print as" methods as
        # it returns a list instead of a string.
        return lines

    @staticmethod
    def print_as_port(data: common_lang.Port):
        """Returns a string with the port formatted as a port."""
        # Trailing semicolon provided by calling routine.
        line = '{} : {} {}'.format(data.name, data.mode, data.type)
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
    def parse_str(gen_str):
        """Attempts to extract the information from a generic interface."""
        data = common_lang.Generic()

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
            return

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
    def print_as_generic(data):
        """Returns a string with the generic interface as a generic."""
        line = '{} : {}'.format(data.name, data.type)
        return line

    @staticmethod
    def print_as_genmap(data):
        """Returns a string with the generic interface as a generic map."""
        line = '{} => {}'.format(data.name, data.name)
        return line

    @staticmethod
    def print_as_constant(data):
        """Returns a string with the generic interface as a constant."""
        # So... generic doesn't necessarily have to have a default value
        # even though it should.  So this requires a little detective work
        # to know whether to include the whole line or add in the necessary
        # constant definition.
        s = re.search(r':=', data.type, re.I)
        if s:
            line = 'constant {} : {}'.format(data.name, data.type)
        else:
            line = 'constant {} : {} := <value>'.format(data.name, data.type)
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
        parameter_pattern  = re.compile(r'#\s*\((.*?)\)', re.I)
        port_pattern       = re.compile(r'\((.*?)\)', re.I)

        parameter_search   = re.search(parameter_pattern, if_string)

        # The parameter declarations comes first
        if parameter_search:
            parameter_str = Parentheses().extract(if_string[parameter_search.start():])
            # debug("Par str: " + parameter_str)

            # remove the parameters from the string
            if_string = re.sub(parameter_pattern, "", if_string)
            # debug("New if str: " + if_string)

        # Now that all the parameters have been removed, we can look for the ports
        port_search        = re.search(port_pattern, if_string)

        if port_search:
            port_str = Parentheses().extract(if_string[port_search.start():])
            # debug("VhdlPort str: " + port_str)

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
                lines.append(SvPort.print_as_signal(port) + ';')
            align_block_on_re(lines, r':')
            indent_vhdl(lines, 1)
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
            align_block_on_re(lines, r':')
            align_block_on_re(lines, r':=')
            indent_vhdl(lines, 1)
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
        lines.append("{} : entity work.{}".format(inst_name, self.data.name))
        if self.data.if_generics:
            lines.append("generic map (")
            # Put the generics in here.  Join with , and a temp
            # character then split at the temp character.  That
            # should create the lines with semicolons on all but
            # the last.
            gen_strings = []
            for generic in self.data.if_generics:
                gen_strings.append(SvParameter.print_as_genmap(generic))
            gen_strings = ',^'.join(gen_strings).split('^')
            for gen_str in gen_strings:
                lines.append(gen_str)
            lines.append(")")
        if self.data.if_ports:
            lines.append("port map (")
            # Put the ports in here.  Same as before.
            port_strings = []
            for port in self.data.if_ports:
                # Print as portmap returns a list unlike others
                for mapping in SvPort.print_as_portmap(port):
                    port_strings.append(mapping)
            port_strings = ',^'.join(port_strings).split('^')
            for port_str in port_strings:
                lines.append(port_str)
            lines.append(");")

        align_block_on_re(lines, '=>')
        indent_vhdl(lines, 1)

        return '\n'.join(lines)

    def component(self):
        """
        Returns a string with a formatted component
        variation of the interface.3
        """
        # Construct structure
        lines = []
        lines.append("component {} is".format(self.data.name))
        if self.data.if_generics:
            lines.append("generic (")
            # Put the generics in here.  Join with ; and a temp
            # character then split at the temp character.  That
            # should create the lines with semicolons on all but
            # the last.
            gen_strings = []
            for generic in self.data.if_generics:
                gen_strings.append(SvParameter.print_as_generic(generic))
            gen_strings = ';^'.join(gen_strings).split('^')
            for gen_str in gen_strings:
                lines.append(gen_str)
            lines.append(");")
        if self.data.if_ports:
            lines.append("port (")
            # Put the ports in here.  Same as before.
            port_strings = []
            for port in self.data.if_ports:
                port_strings.append(SvPort.print_as_port(port))
            port_strings = ';^'.join(port_strings).split('^')
            for port_str in port_strings:
                lines.append(port_str)
            lines.append(");")
        lines.append("end component {};".format(self.data.name))

        align_block_on_re(lines, ':')
        align_block_on_re(lines, r':\s?(?:in\b|out\b|inout\b|buffer\b)?\s*', 'post')
        align_block_on_re(lines, ':=')
        indent_vhdl(lines, 1)

        return '\n'.join(lines)

    def entity(self):
        """
        Returns a string with the interface written as an
        entity declaration.
        """
        # Construct structure
        lines = []
        lines.append("entity {} is".format(self.data.name))
        if self.data.if_generics:
            lines.append("generic (")
            # Put the generics in here.  Join with ; and a temp
            # character then split at the temp character.  That
            # should create the lines with semicolons on all but
            # the last.
            gen_strings = []
            for generic in self.data.if_generics:
                gen_strings.append(SvParameter.print_as_generic(generic))
            gen_strings = ';^'.join(gen_strings).split('^')
            for gen_str in gen_strings:
                lines.append(gen_str)
            lines.append(");")
        if self.data.if_ports:
            lines.append("port (")
            # Put the ports in here.  Same as before.
            port_strings = []
            for port in self.data.if_ports:
                port_strings.append(SvPort.print_as_port(port))
            port_strings = ';^'.join(port_strings).split('^')
            for port_str in port_strings:
                lines.append(port_str)
            lines.append(");")
        lines.append("end entity {};".format(self.data.name))

        align_block_on_re(lines, ':')
        align_block_on_re(lines, r':\s?(?:in\b|out\b|inout\b|buffer\b)?\s*', 'post')
        align_block_on_re(lines, ':=')
        indent_vhdl(lines, 0)

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
                if port.mode.lower() == 'in':
                    port.mode = 'out'
                elif port.mode.lower() == 'out' or port.mode.lower() == 'buffer':
                    port.mode = 'in'

