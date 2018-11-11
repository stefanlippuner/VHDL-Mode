from unittest import TestCase


class TestSvParameter(TestCase):
    def test_parse_str_invalid(self):
        """"Test invalid strings for paraemter definitions"""
        from VHDLMode.sv_lang import SvParameter as p

        # Empty is not valid
        d = p.parse_str('')
        self.assertEqual(False, d.success)

        # Only a name is not valid
        d = p.parse_str('foo')
        self.assertEqual(False, d.success)

        # Only a name is not valid
        d = p.parse_str('parameter foo')
        self.assertEqual(False, d.success)

    def test_parse_str_valid(self):
        """Test some valid strings for parameters"""
        from VHDLMode.sv_lang import SvParameter as p
        from VHDLMode import common_lang

        d = p.parse_str('parameter bar=8')
        self.assertEqual(True, d.success)
        self.assertEqual(common_lang.GenericKind.VALUE, d.kind)
        self.assertEqual('bar', d.name)

        d = p.parse_str(' parameter bar=8 ')
        self.assertEqual(True, d.success)
        self.assertEqual(common_lang.GenericKind.VALUE, d.kind)
        self.assertEqual('bar', d.name)

        d = p.parse_str('parameter a = 1<<6')
        self.assertEqual(True, d.success)
        self.assertEqual(common_lang.GenericKind.VALUE, d.kind)
        self.assertEqual('a', d.name)

        d = p.parse_str('parameter p1 = 1')
        self.assertEqual(True, d.success)
        self.assertEqual(common_lang.GenericKind.VALUE, d.kind)
        self.assertEqual('p1', d.name)
        self.assertEqual('1', d.default_value)

        d = p.parse_str('parameter logic [5:0] p3 = 5')
        self.assertEqual(True, d.success)
        self.assertEqual(common_lang.GenericKind.VALUE, d.kind)
        self.assertEqual('logic [5:0]', d.type)
        self.assertEqual('p3', d.name)
        self.assertEqual('5', d.default_value)

        d = p.parse_str('parameter type p2 = shortint')
        self.assertEqual(True, d.success)
        self.assertEqual(common_lang.GenericKind.TYPE, d.kind)
        self.assertEqual('p2', d.name)
        self.assertEqual('shortint', d.default_value)

        # Github example (parameter type)
        d = p.parse_str('parameter type LB_PKT_T = syn_lb_seq_item#(LB_DATA_W,LB_ADDR_W)')
        self.assertEqual(True, d.success)
        self.assertEqual(common_lang.GenericKind.TYPE, d.kind)
        self.assertEqual('LB_PKT_T', d.name)
        self.assertEqual('syn_lb_seq_item#(LB_DATA_W,LB_ADDR_W)', d.default_value)

        # Parameter with type-hint
        d = p.parse_str('parameter int SIZE_WIDTH = 3')
        self.assertEqual(True, d.success)
        self.assertEqual('SIZE_WIDTH', d.name)
        self.assertEqual('3', d.default_value)

    def test_print_as_generic(self):
        from VHDLMode.sv_lang import SvParameter as p
        d = p.parse_str('parameter logic [5:0] p3 = 5')
        self.assertEqual('parameter logic [5:0] p3 = 5', p.print_as_generic(d))

    def test_print_as_genmap(self):
        from VHDLMode.sv_lang import SvParameter as p
        d = p.parse_str('parameter logic [5:0] p3 = 5')
        self.assertEqual('p3 = p3', p.print_as_genmap(d))

    def test_print_as_constant(self):
        from VHDLMode.sv_lang import SvParameter as p
        d = p.parse_str('parameter logic [5:0] p3 = 5')
        self.assertEqual('const logic [5:0] p3 = 5', p.print_as_constant(d))

        d = p.parse_str('parameter type p2 = shortint')
        self.assertEqual('typedef shortint p2', p.print_as_constant(d))




