#!/usr/bin/env python
# encoding: utf-8

from collections import deque
from contextlib import contextmanager

from .model import (
    Context, Item, ContantItem, TemplateItem, RegexExprItem,
)
from .utils import (
    CircularRefParseError, ReferenceParseError,
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

    def __init__(self, context):
        self.items = []
        self.context = context
        self.item_mappings = context.items
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
            return
        with self.checking_item(item):
            for i in item.dependencies:
                if i in self.solved_set:
                    continue
                if i == item.name:
                    raise CircularRefParseError(i)
                dependency = self.item_mappings.get(i)
                if not dependency:
                    raise ReferenceParseError(i)
                self.check_item(dependency)

    def check(self):
        for i in self.item_mappings.values():
            self.check_item(i)
            self.solved_set.add(i.name)
            self.items.append(i)

    def __iter__(self):
        if not self.items:
            self.check()
        return iter(self.items)


class BaseParser(object):

    def __init__(self, items=None):
        self.items = items or []

    def parse(self, content):
        context = Context(input=content, items={
            item.name: item
            for item in self.items
        })
        items = deque(ParseOrdering(context))
        while items:
            item = items.pop()
            if item.can_evaluate(context):
                context.values[item.name] = item.evaluate_string(context)
            else:
                items.appendleft(item)
        return context
