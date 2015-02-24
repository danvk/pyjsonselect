from nose.tools import *

from collections import OrderedDict
from jsonselect import jsonselect
from tests.utils import jsonLoadOrdered

def match(sel, obj):
    return list(jsonselect.match(sel, obj))


def test_Types():
    eq_([None], match("null", None))
    eq_([[], []], match("array", { '1': [], '2': [] }))
    eq_([{}, {}], match("object", [ {}, {} ]))
    eq_(["a", "b", "c"], match("string", [ "a", 1, True, None, False, "b", 3.1415, "c" ] ))
    eq_([True, False], match("boolean", [ "a", 1, True, None, False, "b", 3.1415, "c" ] ))
    eq_([1, 3.1415], match("number", [ "a", 1, True, None, False, "b", 3.1415, "c" ] ))


def test_IDs():
    obj=OrderedDict([('foo',"aMatch"), ('bar', [ { 'foo': "anotherMatch" } ]) ])
    eq_(["aMatch", "anotherMatch"], match(".foo", obj))

def test_Descendants():
    eq_([2], match(".foo .bar",    {'foo': { 'baz': 1, 'bar': 2 }, 'bar': 3}))
    eq_([2], match(".foo > .bar",  {'foo': { 'baz': 1, 'bar': 2 }, 'bar': 3}))
    eq_([2], match(".foo > .bar",  {'foo': { 'baz': { 'bar': 4 }, 'bar': 2 }, 'bar': 3}))
    eq_([4, 2], match(".foo .bar",
        jsonLoadOrdered('{"foo": { "baz": { "bar": 4 }, "bar": 2 }, "bar": 3}')))

def test_Grouping():
    eq_([1, True, False, 3.1415], match("number,boolean", [ "a", 1, True, None, False, "b", 3.1415, "c" ] ))
    eq_([1, True, None, False, 3.1415], match("number,boolean,null", [ "a", 1, True, None, False, "b", 3.1415, "c" ] ))
