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


def _runTests(path):
    for i, (json_path, selector_path, output_path) in enumerate(_fileTuples(path)):
        data = jsonLoadOrdered(open(json_path).read())
        selector = open(selector_path).read()
        expected_output = open(output_path).read().strip()

        outputs = []
        jsonselectjs.forEach(selector, data, lambda o: outputs.append(o))
        actual_output = '\n'.join([json.dumps(o, indent=4) for o in outputs])

        # Remove trailing whitespace, see http://bugs.python.org/issue16333
        actual_output = '\n'.join([line.rstrip() for line in actual_output.split('\n')])

        if expected_output != actual_output:
            open('/tmp/expected.txt', 'w').write(expected_output)
            open('/tmp/actual.txt', 'w').write(actual_output)
        eq_(expected_output, actual_output, msg='%s: %s\n%r != %r' % (selector_path, selector.strip(), expected_output, actual_output))

        sys.stderr.write('%s %2d %s: passed\n' % (path, i, selector_path))


def test_level1():
    _runTests('tests/spec/level_1')

def test_level2():
    pass

def test_level3():
    pass
