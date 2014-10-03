from nose.tools import *

import cli
import json


def test_node_to_path():
    obj = json.load(open('tests/data.json'))
    nodes = cli.get_result_nodes('.owner', obj)
    eq_(1, len(nodes))

    eq_(['wut', 'metadata', 'owner'], cli.node_to_path(nodes[0]))

    nodes = cli.get_result_nodes('.foo', obj)
    eq_(1, len(nodes))
    eq_(['foo'], cli.node_to_path(nodes[0]))

    nodes = cli.get_result_nodes('.baz', obj)
    eq_(1, len(nodes))
    eq_(['foo', 2, 'baz'], cli.node_to_path(nodes[0]))


def test_select_path_dict():
    obj = { 'foo': { 'bar': 'baz' }, 'quux': 'wut' }
    out = {}
    cli.select_path(['foo', 'bar'], obj, out)
    eq_({'foo': {'bar': 'baz'}}, out)

    out = {}
    cli.select_path(['quux'], obj, out)
    eq_({'quux': 'wut'}, out)


def test_select_path_int():
    obj = [ 'a', 'b', 'c' ]
    out = []
    cli.select_path([1], obj, out)
    eq_(['a'], out)
    cli.select_path([3], obj, out)
    eq_(['a', 'c'], out)


def test_mixed_select():
    obj = { 'foo': [ { 'bar': 'baz', 'a': 'b' }, { 'x': 'y', 'z': 4 } ] }
    out = {}
    cli.select_path(['foo', 2, 'z'], obj, out)
    eq_({'foo': [{ 'z': 4 }]}, out)

    obj = {'foo': ['bar', {'baz': 'quux'}]}
    out = {}
    cli.select_path(['foo', 1], obj, out)
    eq_({'foo': ['bar']}, out)


def test_nonempty_out():
    '''cli.select_path should preserve any objects already in out_obj.'''
    obj = ['bar', {'baz': 'quux'}]
    out = ['bar']
    cli.select_path([2], obj, out)
    eq_(['bar', {'baz': 'quux'}], out)

    obj = {'foo': ['bar', {'baz': 'quux'}]}
    out = {'foo': ['bar']}

    cli.select_path(['foo', 2], obj, out)
    eq_({'foo': ['bar', {'baz': 'quux'}]}, out)


def test_select_paths():
    obj = json.load(open('tests/data.json'))
    eq_({'foo': ['bar', {'baz': 'quux'}]},
        cli.select_paths([['foo', 1], ['foo', 2, 'baz']], obj))


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
