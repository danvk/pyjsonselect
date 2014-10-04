from nose.tools import *

from jsonselectjs import match

def test_Types():
    eq_([None], match("null", None))
    eq_([[], []], match("array", { '1': [], '2': [] }))
    eq_([{}, {}], match("object", [ {}, {} ]))
    eq_(["a", "b", "c"], match("string", [ "a", 1, True, None, False, "b", 3.1415, "c" ] ))
    eq_([True, False], match("boolean", [ "a", 1, True, None, False, "b", 3.1415, "c" ] ))
    eq_([1, 3.1415], match("number", [ "a", 1, True, None, False, "b", 3.1415, "c" ] ))

