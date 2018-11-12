from unittest import TestCase
import sys

sys.path.append('..')


class TestSVPort(TestCase):

    def test_parse_str_min(self):
        """Test a minimal port definition"""
        from VHDLMode.sv_lang import SvPort

        port = SvPort.parse_str('a')
        self.assertEqual('a', port.name)
        self.assertEqual('logic', port.type)
        self.assertEqual('inout', port.mode)
        self.assertEqual('', port.unpacked_dims)
        self.assertTrue(port.success)

    def test_parse_str_dir(self):
        """Test a port definition with only a direction"""
        from VHDLMode.sv_lang import SvPort

        port = SvPort.parse_str('input foo')
        self.assertEqual('foo', port.name)
        self.assertEqual('logic', port.type)
        self.assertEqual('input', port.mode)
        self.assertEqual('', port.unpacked_dims)

    def test_parse_str_full(self):
        """Test 'full' port definition"""
        from VHDLMode.sv_lang import SvPort

        port = SvPort.parse_str('input logic clk')
        self.assertEqual('clk', port.name)
        self.assertEqual('logic', port.type)
        self.assertEqual('input', port.mode)
        self.assertEqual('', port.unpacked_dims)
        self.assertTrue(port.success)

        port = SvPort.parse_str('output logic [5:0] bar')
        self.assertEqual('bar', port.name)
        self.assertEqual('logic [5:0]', port.type)
        self.assertEqual('output', port.mode)
        self.assertEqual('', port.unpacked_dims)
        self.assertTrue(port.success)

        port = SvPort.parse_str(' output logic [3:0] debug_o ')
        self.assertEqual('debug_o', port.name)
        self.assertEqual('logic [3:0]', port.type)
        self.assertEqual('output', port.mode)
        self.assertEqual('', port.unpacked_dims)
        self.assertTrue(port.success)

        port = SvPort.parse_str('reg[range_hi:range_lo] y')
        self.assertEqual('y', port.name)
        self.assertEqual('reg [range_hi:range_lo]', port.type)
        self.assertEqual('inout', port.mode)
        self.assertEqual('', port.unpacked_dims)
        self.assertTrue(port.success)

        port = SvPort.parse_str('output [(N*2)-1:0] data_result')
        self.assertEqual('data_result', port.name)
        self.assertEqual('[(N*2)-1:0]', port.type)
        self.assertEqual('output', port.mode)
        self.assertEqual('', port.unpacked_dims)
        self.assertTrue(port.success)

        port = SvPort.parse_str('inout [14:0]DDR_addr')
        self.assertEqual('DDR_addr', port.name)
        self.assertEqual('[14:0]', port.type)
        self.assertEqual('inout', port.mode)
        self.assertEqual('', port.unpacked_dims)
        self.assertTrue(port.success)

        port = SvPort.parse_str('inout logic [54-1:0] FIXED_IO_mio')
        self.assertEqual('FIXED_IO_mio', port.name)
        self.assertEqual('logic [54-1:0]', port.type)
        self.assertEqual('inout', port.mode)
        self.assertEqual('', port.unpacked_dims)
        self.assertTrue(port.success)

        port = SvPort.parse_str('inout wire [4 - 1 : 0 ] mem_dqs')
        self.assertEqual('mem_dqs', port.name)
        self.assertEqual('wire [4 - 1 : 0 ]', port.type)
        self.assertEqual('inout', port.mode)
        self.assertEqual('', port.unpacked_dims)
        self.assertTrue(port.success)

    def test_parse_str_unpacked(self):
        """Test ports with unpacked dimensions"""
        from VHDLMode.sv_lang import SvPort
        port = SvPort.parse_str('reg unpacked_array [7:0]')
        self.assertEqual('unpacked_array', port.name)
        self.assertEqual('reg', port.type)
        self.assertEqual('inout', port.mode)
        self.assertEqual('[7:0]', port.unpacked_dims)
        self.assertTrue(port.success)

        port = SvPort.parse_str('input int [7:0] y[range_hi:range_lo]')
        self.assertEqual('y', port.name)
        self.assertEqual('int [7:0]', port.type)
        self.assertEqual('input', port.mode)
        self.assertEqual('[range_hi:range_lo]', port.unpacked_dims)
        self.assertTrue(port.success)

        port = SvPort.parse_str('input int a[5]')
        self.assertEqual('a', port.name)
        self.assertEqual('int', port.type)
        self.assertEqual('input', port.mode)
        self.assertEqual('[5]', port.unpacked_dims)
        self.assertTrue(port.success)

        port = SvPort.parse_str('input int [7:0] y[foo bar : 123][7:6][1:2][4]')
        self.assertEqual('y', port.name)
        self.assertEqual('int [7:0]', port.type)
        self.assertEqual('input', port.mode)
        self.assertEqual('[foo bar : 123][7:6][1:2][4]', port.unpacked_dims)
        self.assertTrue(port.success)

    def test_print_as_signal(self):
        from VHDLMode.sv_lang import SvPort
        data = SvPort.parse_str('input int [7:0] y[range_hi:range_lo]')
        self.assertEqual('int [7:0] y[range_hi:range_lo]', SvPort.print_as_signal(data))

    def test_print_as_portmap(self):
        from VHDLMode.sv_lang import SvPort
        data = SvPort.parse_str('input int [7:0] y[range_hi:range_lo]')
        self.assertEqual(['.y ( y )'], SvPort.print_as_portmap(data))

    def test_print_as_port(self):
        from VHDLMode.sv_lang import SvPort
        data = SvPort.parse_str('input int [7:0] y[range_hi:range_lo]')
        self.assertEqual('input int [7:0] y[range_hi:range_lo]', SvPort.print_as_port(data))



