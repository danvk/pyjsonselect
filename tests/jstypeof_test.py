from nose.tools import *

from jsonselect import _jsTypeof


def test_jsTypeof():
    eq_('object', _jsTypeof(None))
    eq_('number', _jsTypeof(10))
    eq_('number', _jsTypeof(10.0))
    eq_('boolean', _jsTypeof(True))
    eq_('boolean', _jsTypeof(False))
    eq_('string', _jsTypeof(''))
    eq_('string', _jsTypeof('hello!'))
    eq_('string', _jsTypeof(u'hello!'))
    eq_('object', _jsTypeof(['a', 'b', 'c']))
    eq_('object', _jsTypeof([]))
    eq_('object', _jsTypeof({}))
    eq_('object', _jsTypeof({'a': 'b'}))
