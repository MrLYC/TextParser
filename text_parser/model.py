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
        ("context", None),

        ("default", undefined),
        ("input", None),
        ("type", TYPE),
        ("name", ""),
    )

    def __init__(self, value, dependencies=None, **kwargs):
        self.context = None
        self.value = value
        self.set_dependencies(dependencies)

        params = dict(self.DEFAULT_ATTRS)
        params.update(kwargs)

        for attr, val in params.items():
            setattr(self, attr, val)

        self.init()

    def init(self):
        pass

    def set_context(self, context):
        self.context = context

    def set_dependencies(self, dependencies):
        self.dependencies = tuple(dependencies or ())
        if not self.dependencies:
            return

        context_items = self.context.items
        for i in self.dependencies:
            if i == self.name:
                raise CircularRefParseError(i)
            if i not in context_items:
                raise ReferenceParseError(i)

    def can_evaluate(self):
        context_values = self.context.values
        for i in self.dependencies:
            if i not in context_values:
                return False
        return True

    def get_value(self):
        return self.default

    def evaluate(self):
        value = self.get_value()
        if value is undefined:
            raise ParseValueError(self.name)
        return value

    def to_string(self):
        return force_text(self.evaluate())


class ContantItem(Item):
    TYPE = "contant"
    DEFAULT_ATTRS = Item.DEFAULT_ATTRS + (
        ("type", TYPE),
    )

    def get_value(self):
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

    def set_context(self, context):
        super(TemplateItem, self).set_context(context)
        self.set_dependencies(
            var for is_var, var in self.iter_value()
            if is_var
        )

    def iter_value(self):
        is_var = False
        for part in self.template:
            yield is_var, part
            is_var = not is_var

    def get_value(self):
        parts = []
        values = self.context.values
        for is_var, part in self.iter_value():
            if is_var:
                part = values.get(part)
            parts.append(force_text(part))
        return "".join(parts)


class ExprItem(Item):
    DEFAULT_ATTRS = Item.DEFAULT_ATTRS + (
        ("pattern", None),
    )

    def get_input(self):
        input_ = self.input
        if not input_:
            return self.context.input
        return self.context.values.get(input_, u"")


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

    def get_value(self):
        input_ = self.get_input()
        match = self.pattern.search(input_)
        if not match:
            return self.default
        groups = match.groups()
        if not groups:
            return undefined
        return groups[0]
