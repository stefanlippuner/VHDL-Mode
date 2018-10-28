from unittest import TestCase


def get_ifs():
    from VHDLMode.sv_lang import SVInterface
    from VHDLMode.vhdl_lang import VhdlInterface

    if_sv = SVInterface()
    # #(parameter integer a = 5, parameter integer b = 3)
    if_sv.parse_block(
        """module foobar            
        (input integer a, output integer b, input logic c);
        // ...
        endmodule""")

    if_vhdl = VhdlInterface()

    # generic(
    #     a: integer:= 5;
    #     b: integer:= 3
    # );
    if_vhdl.parse_block(
        """
        entity foobar is
        port (
            a     : in  integer;
            b     : out integer;
            c     : in std_logic           
        );
        end entity foobar
        """
    )

    return if_sv.data, if_vhdl.data


class TestTranslation(TestCase):
    def test_interface_vhdl_to_sv(self):
        from VHDLMode.translation import Translation
        (if_sv_exp, if_vhdl) = get_ifs()
        if_sv_act = Translation.interface_vhdl_to_sv(if_vhdl)
        self.assertEqual(if_sv_exp.name, if_sv_act.name)
        self.assertEqual(if_sv_exp.if_ports, if_sv_act.if_ports)

    def test_interface_sv_to_vhdl(self):
        from VHDLMode.translation import Translation
        (if_sv, if_vhdl_exp) = get_ifs()
        if_vhdl_act = Translation.interface_sv_to_vhdl(if_sv)
        self.assertEqual(if_vhdl_exp.if_ports, if_vhdl_act.if_ports)
        self.assertEqual(if_vhdl_exp.name, if_vhdl_act.name)

    def test_generic_sv_to_vhdl(self):
        from VHDLMode.translation import Translation
        from VHDLMode.common_lang import Generic

        gen_sv = Generic()
        gen_sv.name = 'bar'
        gen_sv.default_value = '5'
        gen_sv.type = 'reg [6799:0]'
        gen_sv.success = True

        gen_vhdl = Translation.generic_sv_to_vhdl(gen_sv)
        self.assertEqual('bar', gen_vhdl.name)
        self.assertEqual('5', gen_vhdl.default_value)
        self.assertEqual('std_logic_vector(6799 downto 0)', gen_vhdl.type)
        self.assertEqual(True, gen_vhdl.success)

    def test_generic_vhdl_to_sv(self):
        from VHDLMode.translation import Translation
        from VHDLMode.common_lang import Generic

        gen_vhdl = Generic()
        gen_vhdl.name = 'foo'
        gen_vhdl.default_value = '5'
        gen_vhdl.type = 'std_logic_vector(31 downto 0)'
        gen_vhdl.success = True

        gen_sv = Translation.generic_vhdl_to_sv(gen_vhdl)
        self.assertEqual('foo', gen_sv.name)
        self.assertEqual('5', gen_sv.default_value)
        self.assertEqual('logic [31:0]', gen_sv.type)
        self.assertEqual(True, gen_sv.success)

    def test_port_sv_to_vhdl(self):
        from VHDLMode.translation import Translation
        from VHDLMode.common_lang import Port

        port_sv = Port()
        port_sv.name = 'bar'
        port_sv.mode = 'input'
        port_sv.type = 'reg [6799:0]'
        port_sv.success = True

        port_vhdl = Translation.port_sv_to_vhdl(port_sv)
        self.assertEqual('bar', port_vhdl.name)
        self.assertEqual('in', port_vhdl.mode)
        self.assertEqual('std_logic_vector(6799 downto 0)', port_vhdl.type)
        self.assertEqual(True, port_vhdl.success)

    def test_port_vhdl_to_sv(self):
        from VHDLMode.translation import Translation
        from VHDLMode.common_lang import Port

        port_vhdl = Port()
        port_vhdl.name = 'foo'
        port_vhdl.mode = 'in'
        port_vhdl.type = 'std_logic_vector(31 downto 0)'
        port_vhdl.success = True

        port_sv = Translation.port_vhdl_to_sv(port_vhdl)
        self.assertEqual('foo', port_sv.name)
        self.assertEqual('input', port_sv.mode)
        self.assertEqual('logic [31:0]', port_sv.type)
        self.assertEqual(True, port_sv.success)

    def test_mode_sv_to_vhdl(self):
        from VHDLMode.translation import Translation
        self.assertEqual('in', Translation.mode_sv_to_vhdl('input'))
        self.assertEqual('out', Translation.mode_sv_to_vhdl('output'))
        self.assertEqual('inout', Translation.mode_sv_to_vhdl('inout'))
        self.assertEqual('ERR', Translation.mode_sv_to_vhdl('foo'))

    def test_mode_vhdl_to_sv(self):
        from VHDLMode.translation import Translation
        self.assertEqual('input', Translation.mode_vhdl_to_sv('in'))
        self.assertEqual('output', Translation.mode_vhdl_to_sv('out'))
        self.assertEqual('inout', Translation.mode_vhdl_to_sv('inout'))
        self.assertEqual('ERR', Translation.mode_vhdl_to_sv('bar'))

    def test_type_sv_to_vhdl_scalar(self):
        from VHDLMode.translation import Translation
        self.assertEqual('integer', Translation.type_sv_to_vhdl('int'))
        self.assertEqual('integer', Translation.type_sv_to_vhdl('integer'))
        self.assertEqual('std_logic', Translation.type_sv_to_vhdl('reg'))
        self.assertEqual('std_logic', Translation.type_sv_to_vhdl('logic'))
        self.assertEqual('std_logic', Translation.type_sv_to_vhdl('bit'))
        self.assertEqual('ERR', Translation.type_sv_to_vhdl('fubar'))

    def test_type_sv_to_vhdl_vector(self):
        from VHDLMode.translation import Translation
        self.assertEqual('std_logic_vector(31 downto 0)', Translation.type_sv_to_vhdl('logic [31:0]'))
        self.assertEqual('std_logic_vector(5 downto 2)', Translation.type_sv_to_vhdl('reg [5:2]'))
        self.assertEqual('std_logic_vector(0 downto 0)', Translation.type_sv_to_vhdl('reg [0:0]'))

    def test_type_vhdl_to_sv_scalar(self):
        from VHDLMode.translation import Translation
        self.assertEqual('integer', Translation.type_vhdl_to_sv('integer'))
        self.assertEqual('integer', Translation.type_vhdl_to_sv('natural'))
        self.assertEqual('integer', Translation.type_vhdl_to_sv('positive'))
        self.assertEqual('logic', Translation.type_vhdl_to_sv('bit'))
        self.assertEqual('logic', Translation.type_vhdl_to_sv('std_logic'))
        self.assertEqual('logic', Translation.type_vhdl_to_sv('std_ulogic'))
        self.assertEqual('ERR', Translation.type_vhdl_to_sv('foobar'))

    def test_type_vhdl_to_sv_vector(self):
        from VHDLMode.translation import Translation
        self.assertEqual('logic [31:0]', Translation.type_vhdl_to_sv('std_logic_vector(31 downto 0)'))
        self.assertEqual('logic [7:2]', Translation.type_vhdl_to_sv('std_logic_vector(7 downto 2)'))
        self.assertEqual('logic [2:2]', Translation.type_vhdl_to_sv('std_logic_vector(2 downto 2)'))
