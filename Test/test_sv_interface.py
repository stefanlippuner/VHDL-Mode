from unittest import TestCase
import unittest


class TestSVInterface(TestCase):
    def test_interface_start(self):
        from VHDLMode.sv_lang import SVInterface

        interface = SVInterface()
        a = interface.interface_start('a b')
        self.assertIsNone(interface.interface_start('a b'))
        self.assertIsNone(interface.interface_start('entity'))
        self.assertIsNone(interface.interface_start('endmodule'))

        start = interface.interface_start('module foo')
        self.assertIsNotNone(start)
        self.assertEqual('foo', interface.name())

        start = interface.interface_start('     module two (a, bar)')
        self.assertIsNotNone(start)
        self.assertEqual('two', interface.name())

    def test_interface_end(self):
        from VHDLMode.sv_lang import SVInterface

        interface = SVInterface()
        a = interface.interface_end('a b')
        self.assertIsNone(interface.interface_end('a b'))
        self.assertIsNone(interface.interface_end('entity'))
        self.assertIsNone(interface.interface_end('module foo'))

        start = interface.interface_end('endmodule foo')
        self.assertIsNotNone(start)

        start = interface.interface_end('     endmodule // two')
        self.assertIsNotNone(start)

    def test_strip_comments(self):

        from VHDLMode.sv_lang import SVInterface

        interface = SVInterface()
        self.assertEqual('', interface.strip_comments(''), 'empty')
        self.assertEqual('a', interface.strip_comments('a'), 'simple')
        self.assertEqual('/a', interface.strip_comments('/a'), 'slash')
        self.assertEqual('\n', interface.strip_comments('//a'), 'comment')
        self.assertEqual('a\n', interface.strip_comments('a//b'), 'end comment')
        self.assertEqual('a\nc', interface.strip_comments('a//b\nc'), 'newline comment')

    def test_strip_whitespace(self):
        from VHDLMode.sv_lang import SVInterface
        interface = SVInterface()

        self.assertEqual('', interface.strip_whitespace(''), 'empty')
        self.assertEqual('a', interface.strip_whitespace('a'), 'simple')
        self.assertEqual(' ', interface.strip_whitespace('      '), 'spaces')
        self.assertEqual(' ', interface.strip_whitespace('\t\t\t'), 'tabs')
        self.assertEqual(' ', interface.strip_whitespace('\n\n\n'), 'newlines')
        self.assertEqual('a b', interface.strip_whitespace('a      \tb'), 'words 0')
        self.assertEqual('a b', interface.strip_whitespace('a      \nb'), 'words 1')

    def test_parse_block_param(self):
        from VHDLMode.sv_lang import SVInterface
        interface = SVInterface()

        data = interface.parse_block(
            """module m
            #(parameter a = 5, parameter type b = int)            
            (input int a, output int b, input logic c);
            // ...
            endmodule""")

        self.assertEqual(2, len(data.if_generics))
        self.assertEqual('a', data.if_generics[0].name)
        self.assertEqual('5', data.if_generics[0].default_value)
        self.assertEqual('b', data.if_generics[1].name)
        self.assertEqual('int', data.if_generics[1].default_value)

        self.assertEqual(3, len(data.if_ports))
        self.assertEqual('a', data.if_ports[0].name)
        self.assertEqual('input', data.if_ports[0].mode)
        self.assertEqual('int', data.if_ports[0].type)
        self.assertEqual('b', data.if_ports[1].name)
        self.assertEqual('output', data.if_ports[1].mode)
        self.assertEqual('int', data.if_ports[1].type)
        self.assertEqual('c', data.if_ports[2].name)
        self.assertEqual('input', data.if_ports[2].mode)
        self.assertEqual('logic', data.if_ports[2].type)

    def test_parse_block_body(self):
        from VHDLMode.sv_lang import SVInterface
        interface = SVInterface()

        interface.parse_block(
            """module m (a,b,c,d);
            input int a;
            input [4:0] b;
            output reg [3:0] c;
            input d;
            // ...
            endmodule""")

        self.assertEqual([], interface.data.if_generics, 'trivial param')
        self.assertEqual(4, len(interface.data.if_ports), 'trivial port count')

        self.assertEqual('a',           interface.data.if_ports[0].name)
        self.assertEqual('input',       interface.data.if_ports[0].mode)
        self.assertEqual('int',         interface.data.if_ports[0].type)
        self.assertEqual(True,          interface.data.if_ports[0].success)

        self.assertEqual('b',           interface.data.if_ports[1].name)
        self.assertEqual('input',       interface.data.if_ports[1].mode)
        self.assertEqual('[4:0]',       interface.data.if_ports[1].type)
        self.assertEqual(True,          interface.data.if_ports[1].success)

        self.assertEqual('c',           interface.data.if_ports[2].name)
        self.assertEqual('output',      interface.data.if_ports[2].mode)
        self.assertEqual('reg [3:0]',   interface.data.if_ports[2].type)
        self.assertEqual(True,          interface.data.if_ports[2].success)

        self.assertEqual('d',           interface.data.if_ports[3].name)
        self.assertEqual('input',       interface.data.if_ports[3].mode)
        self.assertEqual('logic',       interface.data.if_ports[3].type)
        self.assertEqual(True,          interface.data.if_ports[3].success)

    def test_signals(self):
        self.skipTest('Not implemented')

    def test_constants(self):
        self.skipTest('Not implemented')

    def test_instance(self):
        self.skipTest('Not implemented')

    def test_component(self):
        self.skipTest('Not implemented')

    def test_entity(self):
        self.skipTest('Not implemented')

    def test_flatten(self):
        self.skipTest('Not implemented')

    def test_reverse(self):
        self.skipTest('Not implemented')