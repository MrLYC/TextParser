#!/usr/bin/env python
# encoding: utf-8

from collections import deque, OrderedDict
from contextlib import contextmanager

from .model import (
    Context, Item, ContantItem, TemplateItem,
    RegexExprItem, CSSSelectorExprItem, HTMLXPathExprItem,
)
from .utils import (
    CircularRefParseError, ReferenceParseError, ParseValueError,
)


class ItemFactory(object):
    ITEM_TYPE_MAPPINGS = {
        Item.TYPE: Item,
        ContantItem.TYPE: ContantItem,
        TemplateItem.TYPE: TemplateItem,
        RegexExprItem.TYPE: RegexExprItem,
        CSSSelectorExprItem.TYPE: CSSSelectorExprItem,
        HTMLXPathExprItem.TYPE: HTMLXPathExprItem,
    }

    @classmethod
    def get_item(cls, type, **kwargs):
        type_class = cls.ITEM_TYPE_MAPPINGS.get(type)
        if not type_class:
            raise TypeError(type)
        return type_class(type=type, **kwargs)


class ParseOrdering(object):

    def __init__(self, context):
        self.solved_items = OrderedDict()
        self.context = context
        self.dependencies = {}

        for name, item in context.items.items():
            if not item.dependencies:
                self.solved_items[name] = item
            else:
                self.dependencies[name] = deque(item.dependencies)

    def solve_dependencies(self, dependencies):
        old_dependencies = tuple(dependencies)
        solved_once = False
        dependencies.clear()
        for i in old_dependencies:
            if i in self.solved_items:
                solved_once = True
                continue
            if i not in self.dependencies:
                raise ReferenceParseError(self.context, i)
            dependencies.append(i)
        return solved_once

    def check_dependencies(self):
        context = self.context
        solved_once = False
        for name, dependencies in tuple(self.dependencies.items()):
            if not dependencies:
                solved_once = True
                self.solved_items[name] = context.items[name]
                self.dependencies.pop(name)
            else:
                if self.solve_dependencies(dependencies):
                    solved_once = True
        return solved_once

    def check(self):
        while self.dependencies:
            if not self.check_dependencies():
                raise CircularRefParseError(self.context)

    def __iter__(self):
        if self.dependencies:
            self.check()
        return iter(self.solved_items.values())


class BaseParser(object):

    def __init__(self, items=None, context=None):
        self.items = items or []
        self.context = context

    @contextmanager
    def parse_context(self, context):
        old_context = self.context
        self.context = context
        try:
            yield
        finally:
            self.context = old_context

    def try_evaluate(self, context, item):
        if item.can_evaluate(context):
            context.values[item.name] = item.evaluate_string(context)
            return True
        return False

    def get_context(self, content):
        return self.context or Context.from_item_list(
            input=content, items=self.items, parser=self,
        )

    def parse(self, content):
        raise NotImplementedError()

    @classmethod
    def from_yaml(cls, yaml_content, *args, **kwargs):
        import yaml

        config = yaml.load(yaml_content)
        items = [
            ItemFactory.get_item(name=n, **i)
            for n, i in config["items"].items()
        ]
        return cls(items=items, *args, **kwargs)


class ContextOptimizeMixin(object):

    def optimize_context(self, context):
        ordering_items = [
            (i.name, i)
            for i in ParseOrdering(context)
        ]
        context.set_items(ordering_items)
        return context

    def get_context(self, content):
        context = super(ContextOptimizeMixin, self).get_context(content)
        return self.optimize_context(context)


class LoopParseMixin(object):

    def parse(self, content):
        context = self.get_context(content)
        items = deque(context.items.values())
        if not items:
            return

        sentry = None
        while items:
            item = items.popleft()
            if self.try_evaluate(context, item):
                if item is sentry:
                    sentry = None
            else:
                if item is sentry:
                    raise ParseValueError(context, item.name)
                elif not sentry:
                    sentry = item
                items.appendleft(item)

        return context


class SimpleParseMixin(object):

    def parse(self, content):
        context = self.get_context(content)
        for name, item in context.items.items():
            if not self.try_evaluate(context, item):
                raise ParseValueError(context, name)
        return context


class ContextOptimizeBaseParser(ContextOptimizeMixin, BaseParser):
    pass


class SimpleParser(SimpleParseMixin, BaseParser):
    pass


class QuickParser(SimpleParseMixin, ContextOptimizeBaseParser):
    pass


class SimpleLoopParser(LoopParseMixin, BaseParser):
    pass


class LoopParser(LoopParseMixin, ContextOptimizeBaseParser):
    pass
