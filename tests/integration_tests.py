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
    for spec in specs:
        args = load_commented_json(spec)
        expected = load_commented_json(spec.replace('.spec', '.out'))
        actual = cli.run(args)
        eq_(expected, actual)
