#!/usr/bin/env python
# encoding: utf-8

from collections import deque

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
        items = deque(self.items)
        while items:
            item = items.pop()
            if item.can_evaluate():
                context.values[item.name] = item.evaluate()
            else:
                items.appendleft(item)
