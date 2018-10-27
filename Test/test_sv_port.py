from unittest import TestCase
import sys

sys.path.append('..')


class TestSVPort(TestCase):

    def test_parse_str_min(self):
        """Test a minimal port definition"""
        from sv_lang import SvPort

        port = SvPort('a')
        self.assertEqual('a', port.name)
        self.assertEqual('wire', port.type)
        self.assertEqual('inout', port.mode)

    def test_parse_str_dir(self):
        """Test a port definition with only a direction"""
        from sv_lang import SvPort

        port = SvPort('input foo')
        self.assertEqual('foo', port.name)
        self.assertEqual('wire', port.type)
        self.assertEqual('input', port.mode)

    def test_parse_str_full(self):
        """Test 'full' port definition"""
        from sv_lang import SvPort

        port = SvPort('output logic [5:0] bar')
        self.assertEqual('bar', port.name)
        self.assertEqual('logic [5:0]', port.type)
        self.assertEqual('output', port.mode)
