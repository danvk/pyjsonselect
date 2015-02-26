from nose.tools import *
from collections import OrderedDict
import sys

from jsonselect import jsonselect

def test_abort():
    '''Explicitly stopping the iterator should stop the search.'''
    obj = [0, 1, 2, 3, 4, 5, 6]
    iterator = jsonselect.match('number', obj)
    out = []
    for v in iterator:
        out.append(v)
        if v == 3:
            iterator.close()

    eq_([0, 1, 2, 3], out)


def test_ignore_subtree():
    obj = OrderedDict([('foo', [1, 2, 3]), ('bar', [4, 5, 6] ) ])
    out = []

    def bail(obj, matches):
        return matches and (obj == [1, 2, 3] or obj == [4, 5, 6])

    iterator = jsonselect.match('*', obj, bailout_fn=bail)
    for v in iterator:
        out.append(v)
    eq_([[1, 2, 3], [4, 5, 6], obj], out)
