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

        expected = """    m m_1 #(
        .alpha ( alpha ),
        .beta  ( beta  )
    ) (
        .a           ( a           ),
        .b           ( b           ),
        .ccccccccccc ( ccccccccccc )
    );"""
        indent_sv(lines, initial=1)
        self.assertEqual(expected.split('\n'), lines)