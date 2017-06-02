#!/usr/bin/env python
# encoding: utf-8

from collections import deque
from contextlib import contextmanager

from .model import (
    Context, Item, ContantItem, TemplateItem, RegexExprItem,
)
from .utils import (
    undefined,
    ParseValueError, CircularRefParseError, ReferenceParseError,
)


class ItemFactory(object):
    ITEM_TYPE_MAPPINGS = {
        Item.TYPE: Item,
        ContantItem.TYPE: ContantItem,
        TemplateItem.TYPE: TemplateItem,
        RegexExprItem.TYPE: RegexExprItem,
    }

    @classmethod
    def get_item(cls, type, **kwargs):
        type_class = cls.ITEM_TYPE_MAPPINGS.get(type) or Item
        return type_class(type=type, **kwargs)


class ParseOrdering(object):

    def __init__(self, items):
        self.items = []
        self.item_mappings = {
            i.name: i for i in items
        }
        self.solved_set = set()
        self.checking_set = set()

    @contextmanager
    def checking_item(self, item):
        if item.name in self.checking_set:
            raise CircularRefParseError(item.name)
        try:
            yield self.checking_set.add(item.name)
        finally:
            self.checking_set.remove(item.name)

    def check_item(self, item):
        if item.name in self.solved_set:
            return True
        with self.checking_item(item):
            for i in item.dependencies:
                if (
                    i not in self.solved_set
                    and not self.check_item(self.item_mappings[i])
                ):
                    return False
            return True

    def check(self):
        for i in self.item_mappings.values():
            if self.check_item(i):
                self.solved_set.add(i.name)
                self.items.append(i)

    def __iter__(self):
        if not self.items:
            self.check()
        return iter(self.items)


class BaseParser(object):

    def __init__(self, items=None):
        self.items = items or []
        context = self.context = Context(items={
            item.name: item
            for item in items
        })

        for item in self.items:
            item.set_context(context)

    def set_context(self, context):
        self.context = context
        for i in self.items:
            i.set_context(context)

    def feed(self, content):
        context = self.context
        context.input = content
        items = deque(ParseOrdering(self.items))
        while items:
            item = items.pop()
            if item.can_evaluate():
                context.values[item.name] = item.evaluate()
            else:
                items.appendleft(item)
