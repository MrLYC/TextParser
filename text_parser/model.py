#!/usr/bin/env python
# encoding: utf-8

import re

from .utils import (
    undefined, force_text,
    ParseValueError, CircularRefParseError, ReferenceParseError,
)


class Context(object):

    def __init__(self, input=None, items=None, values=None):
        self.input = input
        self.items = items or {}
        self.values = values or {}


class Item(object):
    TYPE = ""
    DEFAULT_ATTRS = (
        ("default", undefined),
        ("input", None),
        ("type", TYPE),
        ("name", ""),
    )

    def __init__(self, value, dependencies=None, **kwargs):
        self.value = value
        self.dependencies = dependencies or []

        params = dict(self.DEFAULT_ATTRS)
        params.update(kwargs)

        for attr, val in params.items():
            setattr(self, attr, val)

        self.init()

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
            raise ParseValueError(self.name)
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
            return self.default
        groups = match.groups()
        if not groups:
            return undefined
        return groups[0]
