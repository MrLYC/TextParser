# encoding: utf-8

from unittest import TestCase

from text_parser import utils


class TestUtils(TestCase):

    def test_force_text(self):
        self.assertEqual(utils.force_text(1), u"1")
        self.assertEqual(
            utils.force_text(u"测试".encode("utf-8")),
            u"测试",
        )
        self.assertEqual(utils.force_text(u"测试"), u"测试")
