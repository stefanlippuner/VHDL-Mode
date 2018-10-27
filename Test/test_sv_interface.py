from unittest import TestCase
import sys

sys.path.append('..')


class TestSVInterface(TestCase):
    def test_interface_start(self):
        self.fail()

    def test_interface_end(self):
        self.fail()

    def test_strip_comments(self):
        from sv_lang import SVInterface

        interface = SVInterface()
        self.assertEqual('', interface.strip_comments(''), 'empty')
        self.assertEqual('a', interface.strip_comments('a'), 'simple')
        self.assertEqual('/a', interface.strip_comments('/a'), 'slash')
        self.assertEqual('\n', interface.strip_comments('//a'), 'comment')
        self.assertEqual('a\n', interface.strip_comments('a//b'), 'end comment')
        self.assertEqual('a\nc', interface.strip_comments('a//b\nc'), 'newline comment')

    def test_strip_whitespace(self):
        from sv_lang import SVInterface
        interface = SVInterface()

        self.assertEqual('', interface.strip_whitespace(''), 'empty')
        self.assertEqual('a', interface.strip_whitespace('a'), 'simple')
        self.assertEqual(' ', interface.strip_whitespace('      '), 'spaces')
        self.assertEqual(' ', interface.strip_whitespace('\t\t\t'), 'tabs')
        self.assertEqual(' ', interface.strip_whitespace('\n\n\n'), 'newlines')
        self.assertEqual('a b', interface.strip_whitespace('a      \tb'), 'words 0')
        self.assertEqual('a b', interface.strip_whitespace('a      \nb'), 'words 1')

    def test_parse_block(self):
        from sv_lang import SVInterface
        interface = SVInterface()

        interface.parse_block('module m (a,b,c);\ninput int a,b;\noutput reg [3:0] c;\n// ...\nendmodule')

        self.assertEqual([], interface.data.if_parameters, 'trivial param')
        self.assertEqual(3, len(interface.data.if_ports), 'trivial port count')

        self.assertEqual('a',           interface.data.if_ports[0].name)
        self.assertEqual('input',       interface.data.if_ports[0].mode)
        self.assertEqual('int',         interface.data.if_ports[0].type)
        self.assertEqual(True,          interface.data.if_ports[0].type)

        self.assertEqual('b',           interface.data.if_ports[1].name)
        self.assertEqual('input',       interface.data.if_ports[1].mode)
        self.assertEqual('int',         interface.data.if_ports[1].type)
        self.assertEqual(True,          interface.data.if_ports[1].type)

        self.assertEqual('c',           interface.data.if_ports[2].name)
        self.assertEqual('output',      interface.data.if_ports[2].mode)
        self.assertEqual('reg [3:0]',   interface.data.if_ports[2].type)
        self.assertEqual(True,          interface.data.if_ports[2].type)

    def test_signals(self):
        self.fail()

    def test_constants(self):
        self.fail()

    def test_instance(self):
        self.fail()

    def test_component(self):
        self.fail()

    def test_entity(self):
        self.fail()

    def test_flatten(self):
        self.fail()

    def test_reverse(self):
        self.fail()
