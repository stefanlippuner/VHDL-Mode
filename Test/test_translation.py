from unittest import TestCase


class TestTranslation(TestCase):
    def test_interface_vhdl_to_sv(self):
        self.fail()

    def test_interface_sv_to_vhdl(self):
        self.fail()

    def test_generic_sv_to_vhdl(self):
        self.fail()

    def test_generic_vhdl_to_sv(self):
        self.fail()

    def test_port_sv_to_vhdl(self):
        self.fail()

    def test_port_vhdl_to_sv(self):
        self.fail()
        self.fail()

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
