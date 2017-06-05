#!/usr/bin/env python
# encoding: utf-8

import six


undefined = object()


class ParseError(Exception):
    def __init__(self, context, *args, **kwargs):
        super(ParseError, self).__init__(*args, **kwargs)
        self.context = context


class CircularRefParseError(ParseError):
    pass


class ReferenceParseError(ParseError):
    pass


class ParseValueError(ParseError):
    pass


def force_text(obj, encoding="utf-8", errors="strict"):
    if isinstance(obj, six.text_type):
        return obj
    if not isinstance(obj, six.binary_type):
        obj = str(obj)
    return obj.decode(encoding, errors)


class RegisterDict(dict):
    def register(self, key, force=False):
        key = str(key)
        if not force and key in self:
            raise KeyError("%s was existed" % key)

        def update(obj):
            self[key] = obj
            return obj

        return update
