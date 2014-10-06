from nose.tools import *

import glob
import json
import os
import sys

import cli


def load_commented_json(path):
    lines = open(path).read().split('\n')
    return json.loads('\n'.join(
        [line for line in lines if not line.startswith('#')]))


def test_all():
    specs = glob.glob('tests/*.spec.json')
    for idx, spec in enumerate(specs):
        sys.stderr.write('%2d %s\n' % (idx, spec))
        args = load_commented_json(spec)
        expected = load_commented_json(spec.replace('.spec', '.out'))
        actual = cli.run(args)

        if expected != actual:
            json.dump(expected, open('/tmp/expected.json', 'w'), indent=2, sort_keys=True)
            json.dump(actual, open('/tmp/actual.json', 'w'), indent=2, sort_keys=True)

        eq_(expected, actual)
