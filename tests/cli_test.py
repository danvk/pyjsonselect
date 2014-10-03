from nose.tools import *

import cli
import json


def test_filter_object():
    obj = {'foo': ['bar', {'baz': 'quux'}]}
    cli.filter_object(obj, {id(obj['foo'][0]): cli.KEEP})
    eq_({'foo': ['bar']}, obj)

    obj = {'foo': ['bar', {'baz': 'quux'}]}
    cli.filter_object(obj, {id(obj['foo'][1]['baz']): cli.KEEP})
    eq_({'foo': [{'baz': 'quux'}]}, obj)

    obj = {'foo': ['bar', {'baz': 'quux'}]}
    cli.filter_object(obj, {id(obj['foo']): cli.DELETE})
    eq_({}, obj)

    # knock out a particular field.
    obj = {'foo': ['bar', {'baz': 'quux'}]}
    cli.filter_object(obj, {id(obj['foo'][1]): cli.DELETE}, presumption=cli.KEEP)
    eq_({'foo': ['bar']}, obj)
