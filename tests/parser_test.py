from nose.tools import *

from jsonselectjs import parse

def test_two_ids():
    eq_([9,[{"id":"foo"},{"id":"bar"}]],
        parse('.foo .bar'))
