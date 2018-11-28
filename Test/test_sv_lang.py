"""
Test minor functions from sv_lang.py
"""

from unittest import TestCase


class TestSvLang(TestCase):
    def test_indent_sv(self):
        from VHDLMode.sv_lang import indent_sv

        lines = """m m_1 #(
.alpha ( alpha ),
.beta  ( beta  )
) (
.a           ( a           ),
.b           ( b           ),
.ccccccccccc ( ccccccccccc )
);""".split('\n')

        expected = """\tm m_1 #(
\t\t.alpha ( alpha ),
\t\t.beta  ( beta  )
\t) (
\t\t.a           ( a           ),
\t\t.b           ( b           ),
\t\t.ccccccccccc ( ccccccccccc )
\t);"""
        indent_sv(lines, initial=1)
        self.assertEqual(expected.split('\n'), lines)