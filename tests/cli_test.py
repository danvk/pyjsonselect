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
