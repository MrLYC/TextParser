#!/usr/bin/env python
# encoding: utf-8


undefined = object()


class ParseError(Exception):
    pass


class CircularRefParseError(ParseError):
    pass


class ReferenceParseError(ParseError):
    pass


class ParseValueError(ParseError):
    pass


def force_text(obj):
    if isinstance(obj, (str, unicode)):
        return obj
    return unicode(obj)
