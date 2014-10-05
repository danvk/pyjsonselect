from nose.tools import *

from jsonselectjs import match
from tests.utils import jsonLoadOrdered

def xtest_Types():
    eq_([None], match("null", None))
    eq_([[], []], match("array", { '1': [], '2': [] }))
    eq_([{}, {}], match("object", [ {}, {} ]))
    eq_(["a", "b", "c"], match("string", [ "a", 1, True, None, False, "b", 3.1415, "c" ] ))
    eq_([True, False], match("boolean", [ "a", 1, True, None, False, "b", 3.1415, "c" ] ))
    eq_([1, 3.1415], match("number", [ "a", 1, True, None, False, "b", 3.1415, "c" ] ))


def xtest_IDs():
    eq_(["aMatch", "anotherMatch"], match(".foo", {'foo': "aMatch", 'bar': [ { 'foo': "anotherMatch" } ] }))

def test_Descendants():
    eq_([2], match(".foo .bar",    {'foo': { 'baz': 1, 'bar': 2 }, 'bar': 3}))
    eq_([2], match(".foo > .bar",  {'foo': { 'baz': 1, 'bar': 2 }, 'bar': 3}))
    eq_([2], match(".foo > .bar",  {'foo': { 'baz': { 'bar': 4 }, 'bar': 2 }, 'bar': 3}))
    eq_([4, 2], match(".foo .bar",
        jsonLoadOrdered('{"foo": { "baz": { "bar": 4 }, "bar": 2 }, "bar": 3}')))

def xtest_Grouping():
    eq_([1, True, False, 3.1415], match("number,boolean", [ "a", 1, True, None, False, "b", 3.1415, "c" ] ))
    eq_([1, True, None, False, 3.1415], match("number,boolean,null", [ "a", 1, True, None, False, "b", 3.1415, "c" ] ))
