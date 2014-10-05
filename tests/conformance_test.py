import glob
import os
import re
import sys
import json

from nose.tools import *

from tests.utils import jsonLoadOrdered
import jsonselectjs


def _fileTuples(path):
    '''Returns a list of path tuples (input, selector, output) under path.'''
    tuples = []
    for json_path in glob.glob(os.path.join(path, '*.json')):
        selector_glob = json_path.replace('.json', '_*.selector')
        for selector_path in glob.glob(selector_glob):
            output_path = selector_path.replace('.selector', '.output')
            assert os.path.exists(output_path), output_path
            assert os.path.exists(json_path), json_path
            tuples.append((json_path, selector_path, output_path))
    return tuples


def test_level1():
    for json_path, selector_path, output_path in _fileTuples('tests/spec/level_1'):
        data = jsonLoadOrdered(open(json_path).read())
        selector = open(selector_path).read()
        expected_output = [line.strip() for line in open(output_path) if line.strip()]

        #sys.stderr.write('selector: %s\n' % selector)
        #sys.stderr.write('output: %s\n' % '\n'.join(expected_output))

        actual_output = []
        jsonselectjs.forEach(selector, data,
                             lambda o: actual_output.append(json.dumps(o)))
        eq_(expected_output, actual_output, msg='%s: %s\n%r != %r' % (selector_path, selector.strip(), expected_output, actual_output))

        sys.stderr.write('%s: passed\n' % selector_path)


def test_level2():
    pass

def test_level3():
    pass
