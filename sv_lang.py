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

_debug = True


# ---------------------------------------------------------------------------
def debug(string):
    """
    Some of these functions ended up with a lot of debug output for analyzing
    processing.  I needed a way to turn it on and off.
    """
    if _debug:
        print(string)


# ---------------------------------------------------------------------------
def left_justify(lines):
    """
    Method removes all whitespace at the beginning of a line.
    """
    for i in range(len(lines)):
        lines[i] = re.sub(r"^\s*", '', lines[i])


# ---------------------------------------------------------------
def check_for_comment(line):
    """
    Simple method that will return False if a line does not
    begin with a comment, otherwise True.  Mainly used for
    disabling alignment.
    """
    pattern = r'^\s*--'
    p = re.compile(pattern, re.IGNORECASE)
    s = re.search(p, line)
    return bool(s)


# ---------------------------------------------------------------
def strip_comments(line):
    """
    Removes any inline comment from the line, accounting for
    comment symbols inside of a text string.  Does not account
    for multiline commenting.
    """
    str_p = r'".*?"'
    comment_p = r'\\\\.*$'
    # First check for an inline string.  Will only handle one.
    str_s = re.search(str_p, line)
    # If a string exists, then we break up into searching the
    # beginning and end separately.  Otherwise, just a basic
    # whole line search is fine.
    if str_s:
        comment_s = re.search(comment_p, line[:str_s.start()])
        if comment_s:
            return line[:comment_s.start()]
        else:
            comment_s = re.search(comment_p, line[str_s.end():])
            if comment_s:
                return line[:str_s.end()+comment_s.start()]
            else:
                return line
    else:
        comment_s = re.search(comment_p, line)
        if comment_s:
            return line[:comment_s.start()]
        else:
            return line

# ---------------------------------------------------------------------------
def pad_vhdl_symbols(lines):
    """
    Ensuring that special symbols that later we'll align on have a minimum
    leading and trailing space.  Aids correct alignment.  Leaving it at
    assignment and languaage delimeters for now.
    """
    for i in range(len(lines)):
        if not check_for_comment(lines[i]):
            lines[i] = re.sub(':(?!=)', ' : ',  lines[i])
            lines[i] = re.sub(':=',     ' := ', lines[i])
            lines[i] = re.sub('<=',     ' <= ', lines[i])
            lines[i] = re.sub('=>',     ' => ', lines[i])


# ---------------------------------------------------------------------------
def remove_extra_space(lines):
    """
    Method that takes out extra whitespace in a line.  Avoids
    full line comments and attempts to avoid in-line comments.
    """
    for i in range(len(lines)):
        if not check_for_comment(lines[i]):
            # Check and save off inline comments.
            cs = re.search(r'--.*$', lines[i])
            if cs:
                comment = lines[i][cs.start():]
                code = lines[i][0:cs.start()]
            else:
                comment = ''
                code = lines[i]
            # Compress space in code portion of the line.
            code = re.sub(r'\s+', ' ', code)
            code = re.sub(r'\t', ' ', code)
            lines[i] = code + comment


# ---------------------------------------------------------------
class Parentheses():
    '''
    An object whose purpose is to keep track of parenthesis counts
    and provide helper functions while traversing a text file.

    May be initialized with a two element list indicating the starting
    counts if needed.

    open_cnt and close_cnt represent the current number of unmatched
    open and closing parentheses.

    open_pos and close_pos represent the character position of the UNMATCHED
    open and closing parentheses in the last scanned string.
    '''
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
        '''Given a string, extracts the contents of the next parenthetical
        grouping (including interior parenthetical groups.)'''
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
                end = i - 1
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
class Port():
    """
    This is the class of ports and ways to manipulate ports.
    A port consists of a name (string), a mode (optional) (string),
    and a type (string).
    """
    def __init__(self, port_str):
        self.name = ""
        self.mode = ""  # the direction of the port
        self.type = ""
        self.success = False
        self.parse_str(port_str)

    def parse_str(self, port_str):
        """Searches a string for the port fields."""

        # In a first step, we look for the (optional) port direction
        dir_pattern = r'(?P<dir>input|output|inout?)\s+'
        s_dir = re.search(re.compile(dir_pattern, re.IGNORECASE), port_str)
        if s_dir:
            self.mode = s_dir.group('dir')

            # remove the port direction and any trailing whitespace
            port_str = re.sub(dir_pattern, '', port_str)
        else:
            self.mode = 'inout'

        type_pattern = r'(?P<type>.*?)\s+(?P<name>\S*)$'
        pp = re.compile(type_pattern, re.IGNORECASE)
        s = re.search(pp, port_str)

        if s:
            self.name = s.group('name')
            self.type = s.group('type')
            self.success = True
        else:
            self.type = 'wire'

            if len(port_str) >= 1:
                self.name = port_str
                self.success = True
            else:
                self.success = False

        if self.success:
            print('port name: ' + self.name + ", mode: " + self.mode + ", type: " + self.type)
        else:
            print('vhdl-mode: Could not parse port string: ' + port_str + '.')


    def print_as_signal(self):
        """Returns a string with the port formatted for a signal."""
        # Trailing semicolon provided by calling routine.
        line = 'signal {} : {}'.format(self.name, self.type)
        #print(line)
        return line

    def print_as_portmap(self):
        """Returns a string with the port formatted as a portmap."""
        # A port name might be a comma separated list which
        # needs to be split into several lines.
        # Remove any spaces.
        compact = re.sub(r'\s', '', self.name)
        # Split at commas
        names = compact.split(',')
        lines = []
        for name in names:
            lines.append('{} => {}'.format(name, name))
        # This is a departure from the other "print as" methods as
        # it returns a list instead of a string.
        return lines

    def print_as_port(self):
        """Returns a string with the port formatted as a port."""
        # Trailing semicolon provided by calling routine.
        line = '{} : {} {}'.format(self.name, self.mode, self.type)
        #print(line)
        return line


# ---------------------------------------------------------------
class ModuleParameter():
    """
    This is the class of parameters and ways to manipulate them.
    A generic consists of a name (string), a type (string),
    and a default value (string).
    """
    def __init__(self, gen_str):
        self.name = ""
        self.type = ""
        self.assignment = ""
        self.success = False
        self.parse_str(gen_str)

    def parse_str(self, gen_str):

        #debug("Param parse str: " + gen_str)

        """Attempts to extract the information from a generic interface."""
        # Right now I'm going to punt.  There are so many variations
        # on these that it's difficult to write a RE for it.  Also
        # there are few ways to have to rewrite it.  We will extract
        # a name, and then a type string (which may include defaults)
        parameter_type_patter = r'(?P<ptype>parameter|localparam)\s+(?P<type>\S+?)\s+(?P<name>\S+?)\s*(?:=)\s*(?P<assignment>.*)'
        parameter_pattern = r'(?P<ptype>parameter|localparam)\s+(?P<name>\S+?)\s*(?:=)\s*(?P<assignment>.*)'
        gp = re.compile(parameter_pattern, re.IGNORECASE)
        gpt = re.compile(parameter_type_patter, re.IGNORECASE)
        s = re.search(gp, gen_str)
        st = re.search(gpt, gen_str)
        if st:
            self.name = st.group('name')
            # Sometimes the type has a trailing space.  Eliminating it.
            self.type = st.group('type')
            self.assignment = st.group('assignment')
            self.success = True
        elif s:
            self.name = s.group('name')
            self.type = 'int' # this should actually be deducted from the default, but ...
            self.assignment = s.group('assignment')
            self.success = True
        else:
            print('vhdl-mode: Could not parse generic string: ' + gen_str + '.')
            self.success = False

        if self.success:
            debug("parameter name: " + self.name + ", type: " + self.type + ", assignment: " + self.assignment)

    def print_as_generic(self):
        """Returns a string with the generic interface as a generic."""
        line = '{} : {}'.format(self.name, self.type)
        return line

    def print_as_genmap(self):
        """Returns a string with the generic interface as a generic map."""
        line = '{} => {}'.format(self.name, self.name)
        return line

    def print_as_constant(self):
        '''Returns a string with the generic interface as a constant.'''
        # So... generic doesn't necessarily have to have a default value
        # even though it should.  So this requires a little detective work
        # to know whether to include the whole line or add in the necessary
        # constant definition.
        s = re.search(r':=', self.type, re.I)
        if s:
            line = 'constant {} : {}'.format(self.name, self.type)
        else:
            line = 'constant {} : {} := <value>'.format(self.name, self.type)
        return line

# ---------------------------------------------------------------
class Parameter():
    """
    This is the class of subprogram parameters.  Might ultimately
    replace even Port and ModuleParameter as the pattern has improved
    since starting the package.
    """
    def __init__(self, param_str):
        self.storage = ""
        self.identifier = ""
        self.mode = ""
        self.type = ""
        self.expression = ""
        self.success = False
        self.parse_str(param_str)

    def parse_str(self, param_str):
        """Better regexp should be able to extract everything!"""
        regex = r"^\s*((?P<storage>constant|signal|variable|file)\s*)?((?P<name>.*?)\s*)(?::\s*)((?P<mode>inout\b|in\b|out\b|buffer\b)\s*)?((?P<type>.*?)\s*)((?:\:\=)\s*(?P<expression>.*?)\s*)?$"
        #print('Input: "{}"'.format(param_str))
        s = re.search(regex, param_str)
        if s:
            #print('Storage: "{}", Name: "{}", Mode: "{}", Type: "{}", Expression: "{}"'.format(s.group('storage'), s.group('name'), s.group('mode'), s.group('type'), s.group('expression')))
            if s.group('storage'):
                self.storage = s.group('storage')
            self.identifier = s.group('name')
            if s.group('mode'):
                self.mode = s.group('mode')
            self.type = s.group('type')
            if s.group('expression'):
                self.expression = s.group('expression')
            self.success = True
        else:
            print('vhdl-mode: Could not parse parameter string.')
            self.success = False

    def print_formal(self):
        """Lots of optional parameters, needs to be build up gradually."""
        string = ""
        if self.storage:
            string = string + '{} '.format(self.storage)
        string = string + '{} : '.format(self.identifier)
        if self.mode:
            string = string + '{} '.format(self.mode)
        string = string + '{}'.format(self.type)
        if self.expression:
            string = string + ' := {}'.format(self.expression)
        #print(string)
        return string

    def print_call(self):
        """Super easy transform."""
        string = '{} => {}'.format(self.identifier, self.identifier)
        return string


# ---------------------------------------------------------------
class SVInterface():
    """
    The Interface class contains the essential elements to a
    VHDL interface structure as defined by an entity or component
    declaration.  In addition, it comprises the methods used to
    extract the structural elements from strings passed to it
    from the Sublime Text API routines, and to produce string
    variations on these structures so that the structure can
    be transformed in various ways.
    """
    def __init__(self):
        self.name = ""
        self.type = ""
        self.if_string = ""
        self.if_ports = []
        self.if_parameters = []

    def interface_start(self, line: str):
        """Attempts to identify the start of an interface."""
        # Checks for module starting lines
        head_pattern = r"(?P<type>module|macromodule)\s*(?P<name>\w*)"
        p = re.compile(head_pattern, re.IGNORECASE)
        s = re.search(p, line)
        # debug(line)
        if s:
            # Note, it's returning the horizontal position which
            # is different from the "startpoint" class variable
            # above which is the position in the file.
            self.type = s.group('type')
            self.name = s.group('name')
            debug("Hit at: " + line)
            debug("type: " + self.type + ", name: " + self.name)
            return s.start()
        else:
            return None

    def interface_end(self, line: str):
        """Attempts to identify the end of an interface."""
        # Checks to see if the line passed contains the
        # end string matching the starting type.  The
        # type and name are optional technically.
        tail_pattern = r"endmodule".format(self.type, self.name)
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
        self.if_ports = []
        self.if_parameters = []

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
            # debug("Port str: " + port_str)

        # Now parse the two strings and make them into lists

        # Parse the parameter string
        if parameter_search and parameter_str is not None:
            parameter_list = parameter_str.split(',')
            for item in parameter_list:
                parameter = ModuleParameter(item)
                if parameter.success:
                    self.if_parameters.append(parameter)
        else:
            print('vhdl-mode: No parameters found.')

        # Parse the port string
        if port_search and port_str is not None:
            port_list = port_str.split(',')
            for item in port_list:            
                port = Port(item)
                if port.success:
                    self.if_ports.append(port)
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

    def signals(self):
        """
        This method returns a string that consists of the interface
        listed as signals
        """
        lines = []
        # Construct structure and insert
        if self.if_ports:
            for port in self.if_ports:
                lines.append(port.print_as_signal() + ';')
            align_block_on_re(lines, r':')
            indent_vhdl(lines, 1)
            return '\n'.join(lines)
        else:
            return None

    def constants(self):
        '''
        This method returns the generic portion of the interface
        listed as constants.
        '''
        lines = []
        if self.if_parameters:
            for generic in self.if_parameters:
                lines.append(generic.print_as_constant() + ';')
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
        elif self.name in instances:
            instance_count = len(instances[self.name])
            inst_name = self.name+'_{}'.format(instance_count+1)
            # Check for duplicate name and just increment index until clear.
            while inst_name in instances[self.name]:
                instance_count += 1
                inst_name = self.name+'_{}'.format(instance_count+1)
        else:
            inst_name = self.name+'_1'
        lines = []
        lines.append("{} : entity work.{}".format(inst_name, self.name))
        if self.if_parameters:
            lines.append("generic map (")
            # Put the generics in here.  Join with , and a temp
            # character then split at the temp character.  That
            # should create the lines with semicolons on all but
            # the last.
            gen_strings = []
            for generic in self.if_parameters:
                gen_strings.append(generic.print_as_genmap())
            gen_strings = ',^'.join(gen_strings).split('^')
            for gen_str in gen_strings:
                lines.append(gen_str)
            lines.append(")")
        if self.if_ports:
            lines.append("port map (")
            # Put the ports in here.  Same as before.
            port_strings = []
            for port in self.if_ports:
                # Print as portmap returns a list unlike others
                for mapping in port.print_as_portmap():
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
        lines.append("component {} is".format(self.name))
        if self.if_parameters:
            lines.append("generic (")
            # Put the generics in here.  Join with ; and a temp
            # character then split at the temp character.  That
            # should create the lines with semicolons on all but
            # the last.
            gen_strings = []
            for generic in self.if_parameters:
                gen_strings.append(generic.print_as_generic())
            gen_strings = ';^'.join(gen_strings).split('^')
            for gen_str in gen_strings:
                lines.append(gen_str)
            lines.append(");")
        if self.if_ports:
            lines.append("port (")
            # Put the ports in here.  Same as before.
            port_strings = []
            for port in self.if_ports:
                port_strings.append(port.print_as_port())
            port_strings = ';^'.join(port_strings).split('^')
            for port_str in port_strings:
                lines.append(port_str)
            lines.append(");")
        lines.append("end component {};".format(self.name))

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
        lines.append("entity {} is".format(self.name))
        if self.if_parameters:
            lines.append("generic (")
            # Put the generics in here.  Join with ; and a temp
            # character then split at the temp character.  That
            # should create the lines with semicolons on all but
            # the last.
            gen_strings = []
            for generic in self.if_parameters:
                gen_strings.append(generic.print_as_generic())
            gen_strings = ';^'.join(gen_strings).split('^')
            for gen_str in gen_strings:
                lines.append(gen_str)
            lines.append(");")
        if self.if_ports:
            lines.append("port (")
            # Put the ports in here.  Same as before.
            port_strings = []
            for port in self.if_ports:
                port_strings.append(port.print_as_port())
            port_strings = ';^'.join(port_strings).split('^')
            for port_str in port_strings:
                lines.append(port_str)
            lines.append(");")
        lines.append("end entity {};".format(self.name))

        align_block_on_re(lines, ':')
        align_block_on_re(lines, r':\s?(?:in\b|out\b|inout\b|buffer\b)?\s*', 'post')
        align_block_on_re(lines, ':=')
        indent_vhdl(lines, 0)

        return '\n'.join(lines)

    def flatten(self):
        '''
        Iterates over the generics and ports and if there
        is a line with multiple token names on the same line, will
        make copies of that port with the individual token names.
        '''
        if self.if_parameters:
            new_generics = []
            for generic in self.if_parameters:
                if ',' in generic.name:
                    name_list = re.sub(r'\s*,\s*', ',', generic.name).split(',')
                    for name in name_list:
                        new_generic = copy.copy(generic)
                        new_generic.name = name
                        new_generics.append(new_generic)
                else:
                    new_generics.append(generic)
            self.if_parameters = new_generics
        if self.if_ports:
            new_ports = []
            for port in self.if_ports:
                if ',' in port.name:
                    name_list = re.sub(r'\s*,\s*', ',', port.name).split(',')
                    for name in name_list:
                        new_port = copy.copy(port)
                        new_port.name = name
                        new_ports.append(new_port)
                else:
                    new_ports.append(port)
            self.if_ports = new_ports

    def reverse(self):
        '''
        Iterates over the ports and flips the direction/mode.
        in becomes out
        out and buffer become in
        inout is unchanged.
        '''
        if self.if_ports:
            for port in self.if_ports:
                if port.mode.lower() == 'in':
                    port.mode = 'out'
                elif port.mode.lower() == 'out' or port.mode.lower() == 'buffer':
                    port.mode = 'in'


# ---------------------------------------------------------------
class Subprogram():
    """
    Class that contains information about a VHDL subprogram
    declaration and methods to enable rewriting it in some
    fashion.
    """
    def __init__(self):
        self.name = ""
        self.type = ""
        self.purity = ""
        self.if_string = ""
        self.if_params = []
        self.if_parameters = []
        self.if_return = ""
        self.paren_count = [0, 0]

    def reset(self):
        """Subprograms need a reset simply because there's a lot of
        optional things that change from copy to copy.  In the
        entity/component world, it's a lot more uniform."""
        self.name = ""
        self.type = ""
        self.purity = ""
        self.if_string = ""
        self.if_params = []
        self.if_parameters = []
        self.if_return = ""
        self.paren_count = [0, 0]

    def subprogram_start(self, line):
        """Attempts to identify the start of a subprogram specification."""
        # Resetting the paren count here in case we end up calling this
        # entire command multiple times.  Finding the end depends on it.
        self.paren_count = [0, 0]
        head_pattern = r"((?P<purity>impure|pure)\s+)?(?P<type>procedure|function)\s+(?P<name>\w*)"
        s = re.search(head_pattern, line, re.I)
        if s:
            if s.group('purity'):
                self.purity = s.group('purity')
            self.type = s.group('type')
            self.name = s.group('name')
            return s.start()
        else:
            return None

    def subprogram_end(self, line):
        """Attempts to identify the end of the subprogram specification.
        This is somewhat trickier than finding the end of an entity or
        component simply because there's no end clause.  A procedure
        specification block ends on a semicolon in the case of the
        prototype, and ends on 'is' in the case of a declaration.
        A function ends on return <type>; or return <type> is.  Due to
        the procedure semicolon ending (which will get also used in the
        parameters) we have to match and count parens and only validate
        a tail when all parens are balanced."""
        # Patterns to check.
        proc_tail_pattern = r";|is"
        func_tail_pattern = r"return\s+(?P<rtype>.*?)\s*(;|is)"

        # Find our parenthesis state.
        parens = Parentheses()
        parens.scan(line)

        # If we are unbalanced, then there's nothing to do and return.  Otherwise
        # use the last paren location to trim the line and perform the search.
        if parens.balanced:
            if close_pos:
                new_line = line[parens.close_pos[-1]:]
                offset = close_pos[-1]
            else:
                new_line = line
                offset = 0

            if self.type.lower() == 'function':
                s = re.search(func_tail_pattern, new_line, re.I)
                if s:
                    self.if_return = s.group('rtype')
                    return s.end() + offset
                else:
                    return None
            elif self.type.lower() == 'procedure':
                s = re.search(proc_tail_pattern, new_line, re.I)
                if s:
                    return s.end() + offset
                else:
                    return None
            else:
                return None
        else:
            return None

    def parse_block(self):
        """Chops up the string and extracts the internal declarations."""
        # Remove comments, newlines, and compress spaces.
        self.if_string = re.sub(r'--.*?(\n|$)', r'\n', self.if_string)
        self.if_string = re.sub(r'\n', r'', self.if_string)
        self.if_string = re.sub(r'\s+', r' ', self.if_string)
        # Strip return clause if a function.
        if self.type == 'function':
            func_tail_pattern = r"return\s+(?P<rtype>.*?)\s*(;|is)"
            s = re.search(func_tail_pattern, self.if_string, re.I)
            self.if_string = self.if_string[:s.start()]
        # Extract parameter block.
        start, stop = None, None
        for i in range(len(self.if_string)):
            if self.if_string[i] == '(' and not start:
                start = i+1
            if self.if_string[-i] == ')' and not stop:
                stop = -i
            if start and stop:
                break
        if start and stop:
            self.if_string = self.if_string[start:stop]
            #print(self.if_string)
            param_list = self.if_string.split(';')
            for param_str in param_list:
                param = Parameter(param_str)
                if param.success:
                    self.if_params.append(param)
                    #param.print()
        else:
            print('vhdl-mode: No subprogram parameters found.')

    def print(self):
        """For debug"""
        print('Purity: {}'.format(self.purity))
        print('SP Type: {}'.format(self.type))
        print('SP Name: {}'.format(self.name))
        print('Params: {}'.format(self.if_params))
        print('Return: {}'.format(self.if_return))

    def declaration(self):
        """Constructs a subprogram declaration from the currently
        copied subprogram.  Again there are many optional things
        so construction is piece by piece.  Going to format in
        K&R style. """
        lines = []
        if self.type == 'function':
            if self.if_params:
                if self.purity:
                    lines.append('{} {} {} ('.format(self.purity, self.type, self.name))
                else:
                    lines.append('{} {} ('.format(self.type, self.name))
                param_strings = []
                for param in self.if_params:
                    param_strings.append(param.print_formal())
                param_strings = ';^'.join(param_strings).split('^')
                for param_str in param_strings:
                    lines.append(param_str)
                lines.append(') return {};'.format(self.if_return))
            else:
                if self.purity:
                    lines.append('{} {} {} return {};'.format(self.purity, self.type, self.name, self.rtype))
                else:
                    lines.append('{} {} return {};'.format(self.type, self.name, self.if_return))
        else: # Procedure
            if self.if_params:
                lines.append('{} {} ('.format(self.type, self.name))
                param_strings = []
                for param in self.if_params:

                    param_strings.append(param.print_formal())
                param_strings = ';^'.join(param_strings).split('^')
                for param_str in param_strings:
                    lines.append(param_str)
                lines.append(');')
            else:
                lines.append('{} {};'.format(self.type, self.name))

        align_block_on_re(lines, ':')
        align_block_on_re(lines, r':\s?(?:in\b|out\b|inout\b|buffer\b)?\s*', 'post')
        align_block_on_re(lines, ':=')
        indent_vhdl(lines, 1)

        return '\n'.join(lines)

    def body(self):
        """Constructs a subprogram body from the currently
        copied subprogram.  Again there are many optional things
        so construction is piece by piece.  Going to format in
        K&R style. """
        lines = []
        if self.type == 'function':
            if self.if_params:
                if self.purity:
                    lines.append('{} {} {} ('.format(self.purity, self.type, self.name))
                else:
                    lines.append('{} {} ('.format(self.type, self.name))
                param_strings = []
                for param in self.if_params:
                    param_strings.append(param.print_formal())
                param_strings = ';^'.join(param_strings).split('^')
                for param_str in param_strings:
                    lines.append(param_str)
                lines.append(') return {} is'.format(self.if_return))
            else:
                if self.purity:
                    lines.append('{} {} {} return {} is'.format(self.purity, self.type, self.name, self.rtype))
                else:
                    lines.append('{} {} return {} is'.format(self.type, self.name, self.if_return))
        else: # Procedure
            if self.if_params:
                lines.append('{} {} ('.format(self.type, self.name))
                param_strings = []
                for param in self.if_params:
                    param_strings.append(param.print_formal())
                param_strings = ';^'.join(param_strings).split('^')
                for param_str in param_strings:
                    lines.append(param_str)
                lines.append(') is')
            else:
                lines.append('{} {} is'.format(self.type, self.name))
        lines.append('begin')
        lines.append(' ')
        lines.append('end {} {};'.format(self.type, self.name))

        align_block_on_re(lines, ':')
        align_block_on_re(lines, r':\s?(?:in\b|out\b|inout\b|buffer\b)?\s*', 'post')
        align_block_on_re(lines, ':=')
        indent_vhdl(lines, 1)

        return '\n'.join(lines)

    def call(self):
        """Constructs a subprogram call.  Much simpler than the
        declaration."""
        lines = []
        param_strings = []
        if self.if_params:
            lines.append('{} ('.format(self.name))
            for param in self.if_params:
                param_strings.append(param.print_call())
            param_strings = ',^'.join(param_strings).split('^')
            for param_str in param_strings:
                lines.append(param_str)
            lines.append(');')
        else:
            lines.append('{};'.format(self.name))

        align_block_on_re(lines, '=>')
        indent_vhdl(lines, 1)

        return '\n'.join(lines)

    def flatten(self):
        new_params = []
        if self.if_params:
            for param in self.if_params:
                if ',' in param.identifier:
                    name_list = re.sub(r'\s*,\s*', ',', param.identifier).split(',')
                    for name in name_list:
                        new_param = copy.copy(param)
                        new_param.identifier = name
                        new_params.append(new_param)

                else:
                    new_params.append(param)
            self.if_params = new_params

