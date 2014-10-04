from nose.tools import *

from jsonselectjs import parse, JsonSelectError

def test_Selectors():
    eq_([4, [{'id': "foo"}]], parse(".foo"))
    eq_([8, [{'id': " foo "}]], parse('." foo "'))
    eq_([21, [{'a': 0, 'b': 1, 'id': "foo", 'pf': ":nth-last-child", 'type': "string"}]], parse("string.foo:last-child"))
    eq_([15, [{'id': "xxx@yyy", 'type': "string"}]], parse("string.xxx\\@yyy"))
    with assert_raises(JsonSelectError) as context:
        parse(" ")
    eq_("selector expected in ' '", context.exception.message)

    with assert_raises(JsonSelectError) as context:
        parse("")
    eq_("selector expected", context.exception.message)
