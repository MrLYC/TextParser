# encoding: utf-8

from unittest import TestCase

from text_parser import model
from text_parser import parser
from text_parser import utils


class TestParseOrdering(TestCase):

    def test_check(self):
        context = model.Context.from_item_list([
            model.TemplateItem("${id}", name="title"),
            model.TemplateItem("1", name="value1"),
            model.TemplateItem("i-${value1}-${value2}", name="id"),
            model.ContantItem("2", name="value2"),
        ])
        parse_ordering = parser.ParseOrdering(context)
        parse_ordering.check()
        self.assertEqual(
            [i.name for i in parse_ordering],
            ["value1", "value2", "id", "title"],
        )

    def test_check_error1(self):
        name = str(id(self))
        context = model.Context.from_item_list([
            model.TemplateItem("${%s}" % name, name="title"),
        ])
        parse_ordering = parser.ParseOrdering(context)
        with self.assertRaisesRegexp(utils.ReferenceParseError, name):
            parse_ordering.check()

    def test_check_error2(self):
        context = model.Context.from_item_list([
            model.TemplateItem("${key2}", name="key1"),
            model.TemplateItem("${key1}", name="key2"),
        ])
        parse_ordering = parser.ParseOrdering(context)
        with self.assertRaises(utils.CircularRefParseError):
            parse_ordering.check()

    def test_check_error3(self):
        context = model.Context.from_item_list([
            model.TemplateItem("${key}", name="key"),
        ])
        parse_ordering = parser.ParseOrdering(context)
        with self.assertRaises(utils.CircularRefParseError):
            parse_ordering.check()
