"""
#----------------------------------------------------------------
# VHDL Mode Utility Module
# Contains methods that were useful in more than one location
#----------------------------------------------------------------
"""
import re
import sublime
import os.path

def move_up(self, point):
    """
    Moves up one line, attempting to maintain column position.
    """
    x, y = self.view.rowcol(point)
    if x == 0:
        return self.view.text_point(0, 0)
    else:
        return self.view.text_point(x-1, y)

#----------------------------------------------------------------------------
def move_down(self, point):
    """
    Moves down one line, attempting to maintain column position.
    """
    eof_x, eof_y = self.view.rowcol(self.view.size())
    x, y = self.view.rowcol(point)
    #print('row={} col={} eof_row={} eof_col={}'.format(x, y, eof_x, eof_y))
    if x == eof_x:
        # The size is the number of characters and the point is
        # zero indexed, so subtract one from the size.
        return self.view.size()-1
    else:
        return self.view.text_point(x+1, y)

#----------------------------------------------------------------------------
def move_to_bol(self, point):
    """
    Moves the point to the beginning of the line for searching.
    """
    x, y = self.view.rowcol(point)
    return self.view.text_point(x, 0)

#----------------------------------------------------------------------------
def is_top_line(self, point):
    """
    A simple check for the top line of the file.
    """
    x, y = self.view.rowcol(point)
    return bool(x == 0)

#----------------------------------------------------------------------------
def is_end_line(self, point):
    """
    A simple check for the bottom line of the file
    (not necessarily the end of file.)
    """
    x, y = self.view.rowcol(point)
    # The size is the number of characters and the
    # point is zero indexed, so subtract on from the size
    # for the final character.
    eof_x, eof_y = self.view.rowcol(self.view.size()-1)
    return bool(x == eof_x)

#----------------------------------------------------------------------------
def set_cursor(self, point):
    """
    Just setting the point to a particular location.
    """
    self.view.sel().clear()
    self.view.sel().add(sublime.Region(point))
    self.view.show(point)

#----------------------------------------------------------------------------
def line_at_point(self, point):
    """
    Shorthand string extraction method.
    """
    return self.view.substr(self.view.line(point))

#----------------------------------------------------------------------------
def is_vhdl_file(line):
    """
    Receives a string formatted as identifying the
    language scope of the point.  Scope identifiers all
    end with the language name as the trailing clause,
    so we look for 'vhdl'
    """
    s = re.search(r'vhdl', line)
    return bool(s)

#----------------------------------------------------------------------------
def extract_scopes(self):
    """
    This method scans column zero of each line and extracts
    the scope at that point.  Aids in alignment.
    """
    scope_list = []
    point = 0
    while not is_end_line(self, point):
        scope_list.append(self.view.scope_name(point))
        point = move_down(self, point)
    # One final append for the last line.
    scope_list.append(self.view.scope_name(point))
    # Debug
    for i in range(len(scope_list)):
        print('{}: {}'.format(i, scope_list[i]))
    return scope_list

#----------------------------------------------------------------------------
def get_vhdl_setting(cmd_obj, key):
    '''
    Borrowing an idea from OdatNurd from ST forum, creating a method
    that will return the value of a key and also check to see if
    it's been overridden in project files.  Defaults are handled by
    the supplied sublime-settings file.

    This will actually work on the regular Preferences as well I think
    though might do bad things if the key doesn't exist.
    '''
    # Load the defaults, or user overridden defaults.
    vhdl_settings = sublime.load_settings('vhdl_mode.sublime-settings')
    default = vhdl_settings.get(key, None)
    # Load the view's settings
    view_settings = cmd_obj.view.settings()
    return view_settings.get(key, default)

#----------------------------------------------------------------------------
def scan_instantiations(cmd_obj):
    '''
    Obtaining a list of all regions that contain instantiation labels
    and then creating a dictionary of instantiated components and their
    associated labels.
    '''
    instances = {}
    selector = 'meta.block.instantiation entity.name.label'
    regions = cmd_obj.view.find_by_selector(selector)
    for region in regions:
        line = cmd_obj.view.substr(cmd_obj.view.full_line(region))
        line = re.sub(r'\n', '', line)
        row, col = cmd_obj.view.rowcol(region.begin())
        pattern = r'^\s*(?P<label>\w+)\s*:\s*(?:entity)?\s*((?P<lib>\w+)\.)?(?P<entity>[\w\.]+)'
        s = re.search(pattern, line, re.I)
        if s:
            if s.group('entity') in instances:
                instances[s.group('entity')].append(s.group('label'))
            else:
                instances[s.group('entity')] = [s.group('label')]
        else:
            print('vhdl-mode: Could not match instantiation on line {}'.format(row+1))
    return instances


def get_language_from_filename(filename):
    """
    Attempts to find out the RTL language from a filename
    :param filename: (Path + )Filename
    :return: Either 'vhdl', 'sv', or None
    """

    if not isinstance(filename, str):
        return None
    else:
        path, extension = os.path.splitext(filename)
        if extension == '.vhdl':
            return 'vhdl'
        elif extension == '.sv' or extension == '.v':
            return 'sv'

    return None


# ---------------------------------------------------------------
def check_for_comment(line, lang='vhdl'):
    """
    Simple method that will return False if a line does not
    begin with a comment, otherwise True.  Mainly used for
    disabling alignment.
    """
    if lang == 'vhdl':
        pattern = r'^\s*--'
    elif lang == 'sv':
        pattern = r'^\s*//'

    p = re.compile(pattern, re.IGNORECASE)
    s = re.search(p, line)
    return bool(s)


# ---------------------------------------------------------------
def align_block_on_re(lines, regexp, padside='pre', ignore_comment_lines=True,
                      scope_data=None, lang='vhdl'):
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
            comment_check = check_for_comment(lines[i], lang=lang)

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
                end = i
                pcount -= 1
                break
        if start >= end:
            return None
        else:
            return line[start:end]
