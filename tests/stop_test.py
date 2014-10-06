from nose.tools import *
import sys

import jsonselectjs

def test_abort():
    '''Explicitly stopping the iterator should stop the search.'''
    obj = [0, 1, 2, 3, 4, 5, 6]
    iterator = jsonselectjs.match('number', obj)
    out = []
    for v in iterator:
        out.append(v)
        if v == 3:
            iterator.close()

    eq_([0, 1, 2, 3], out)


def test_iter_order():
    '''Sending an IgnoreSubtree message should prune the search.'''
    obj = { 'foo': [1, 2, 3], 'bar': [4, 5, 6] }
    eq_([obj, [1, 2, 3], 1, 2, 3, [4, 5, 6], 4, 5, 6],
        list(jsonselectjs.match('*', obj, iter_order=jsonselectjs.TopDown)))
    eq_([1, 2, 3, [1, 2, 3], 4, 5, 6, [4, 5, 6], obj],
        list(jsonselectjs.match('*', obj, iter_order=jsonselectjs.BottomUp)))


def test_ignore_subtree():
    obj = { 'foo': [1, 2, 3], 'bar': [4, 5, 6] }
    out = []

    def bail(obj, matches):
        return matches and (obj == [1, 2, 3] or obj == [4, 5, 6])

    iterator = jsonselectjs.match('*', obj, bailout_fn=bail)
    for v in iterator:
        out.append(v)
    eq_([[1, 2, 3], [4, 5, 6], obj], out)
