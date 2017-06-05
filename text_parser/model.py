#!/usr/bin/env python
# encoding: utf-8

import re
import datetime
from collections import OrderedDict

from .utils import (
    undefined, force_text, ParseValueError, RegisterDict,
)


class Context(object):

    def __init__(
        self, input=None, items=None, values=None, parser=None,
        debug=False,
    ):
        self.input = input
        self.values = values or {}
        self.comments = OrderedDict()
        self.parser = parser
        self.debug = debug
        self.set_items(items)

    def set_items(self, items):
        self.items = OrderedDict(items or {})

    def add_comment(self, name, comment):
        comments = self.comments.get(name)
        if comments is None:
            comments = self.comments.setdefault(name, [])
        comments.append(comment)

    @classmethod
    def from_item_list(cls, items, **kwargs):
        return cls(items=[
            (i.name, i) for i in items
        ], **kwargs)


class Item(object):
    TYPE = ""
    DEFAULT_ATTRS = (
        ("default", undefined),
        ("type", TYPE),
    )

    def __init__(
        self, value, dependencies=None, name=None, input=None,
        **kwargs
    ):
        self.name = name or force_text(id(self))
        self.value = value
        self.input = input
        self.dependencies = None

        self.set_dependencies(dependencies)

        params = dict(self.DEFAULT_ATTRS)
        params.update(kwargs)

        for attr, val in params.items():
            setattr(self, attr, val)

        self.init()

    def add_comment(self, context, comment):
        context.add_comment(self.name, comment)

    def set_dependencies(self, dependencies):
        dependencies = list(dependencies or [])
        if self.input:
            dependencies.append(self.input)
        self.dependencies = dependencies

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Item[{self.name}]: type={self.type}>".format(self=self)

    def init(self):
        pass

    def can_evaluate(self, context):
        context_values = context.values
        for i in self.dependencies:
            if i not in context_values:
                return False
        return True

    def get_value(self, context):
        return self.default

    def evaluate(self, context):
        value = self.get_value(context)
        if value is undefined:
            raise ParseValueError(context, self.name)
        return value

    def evaluate_string(self, context):
        return force_text(self.evaluate(context))


class ContantItem(Item):
    TYPE = "contant"
    DEFAULT_ATTRS = Item.DEFAULT_ATTRS + (
        ("type", TYPE),
    )

    def get_value(self, context):
        return self.value


class TemplateItem(Item):
    TYPE = "template"
    DEFAULT_ATTRS = Item.DEFAULT_ATTRS + (
        ("type", TYPE),
        ("default", u""),
    )
    VAR_REGEX = re.compile(r"\${\s*(?P<key>\w+)\s*}")

    def init(self):
        self.template = self.VAR_REGEX.split(self.value)
        self.dependencies.extend(
            var for is_var, var in self.iter_value()
            if is_var
        )

    def iter_value(self):
        is_var = False
        for part in self.template:
            yield is_var, part
            is_var = not is_var

    def get_value(self, context):
        parts = []
        values = context.values
        for is_var, part in self.iter_value():
            if is_var:
                part = values.get(part)
            parts.append(force_text(part))
        return "".join(parts)


class ExprItem(Item):
    DEFAULT_ATTRS = Item.DEFAULT_ATTRS + (
        ("pattern", None),
    )

    def get_input(self, context):
        input_ = self.input
        if not input_:
            return context.input
        return context.values.get(input_, u"")


class RegexExprItem(ExprItem):
    TYPE = "regex"
    DEFAULT_ATTRS = ExprItem.DEFAULT_ATTRS + (
        ("type", TYPE),
        ("flag", "SIM"),
    )
    REGEX_FLAGS = {
        "S": re.S,
        "I": re.I,
        "M": re.M,
        "U": re.U,
    }

    def init(self):
        flag = 0
        for f in self.flag:
            v = self.REGEX_FLAGS.get(f.upper())
            if not v:
                continue
            flag |= v
        self.pattern = re.compile(self.value, flag)

    def get_value(self, context):
        input_ = self.get_input(context)
        match = self.pattern.search(input_)
        if not match:
            self.add_comment(context, "pattern not found")
            return self.default
        groups = match.groups()
        if not groups:
            self.add_comment(context, "groups not found")
            return self.default
        return groups[0]


class CSSSelectorExprItem(ExprItem):
    TYPE = "css-selector"
    DEFAULT_ATTRS = ExprItem.DEFAULT_ATTRS + (
        ("type", TYPE),
    )

    def get_value(self, context):
        from pyquery import PyQuery

        input_ = self.get_input(context)
        pyquery = PyQuery(input_)
        return pyquery(self.value).text()


class HTMLXPathExprItem(ExprItem):
    TYPE = "xpath"
    DEFAULT_ATTRS = ExprItem.DEFAULT_ATTRS + (
        ("type", TYPE),
    )

    def get_value(self, context):
        from lxml import etree

        input_ = self.get_input(context)
        root = etree.HTML(input_)
        result = root.xpath(self.value)
        if not result:
            self.add_comment(context, "pattern not found")
            return self.default
        result = result[0]
        if isinstance(result, etree._Element):
            return etree.tostring(result)
        return result


class FunctionExprItem(ExprItem):
    TYPE = "function"
    DEFAULT_ATTRS = ExprItem.DEFAULT_ATTRS + (
        ("type", "TYPE"),
    )
    FUNCTIONS = RegisterDict()

    def init(self):
        self.function = self.FUNCTIONS.get(self.value)
        if not self.function:
            raise TypeError(self.value)

    def get_value(self, context):
        return self.function(self, context, self.get_input(context))

    @FUNCTIONS.register("trim")
    def func_trim(self, context, input_):
        return input_.strip()

    @FUNCTIONS.register("title")
    def func_title(self, context, input_):
        return input_.title()

    @FUNCTIONS.register("upper")
    def func_upper(self, context, input_):
        return input_.upper()

    @FUNCTIONS.register("lower")
    def func_lower(self, context, input_):
        return input_.lower()

    @FUNCTIONS.register("now")
    def func_now(self, context, input_):
        now = datetime.datetime.now()
        return now.isoformat()

    @FUNCTIONS.register("today")
    def func_today(self, context, input_):
        today = datetime.date.today()
        return today.isoformat()
