# encoding: utf-8

from textwrap import dedent
from unittest import TestCase

from text_parser import model


class TestContext(TestCase):

    def test_init(self):
        context = model.Context()
        context.set_items((
            ("2", None),
            ("3", None),
            ("1", None),
        ))
        self.assertListEqual(list(context.items), ["2", "3", "1"])

        context = model.Context(input="", items=None, values={"a": 1})
        self.assertEqual(context.values["a"], 1)
