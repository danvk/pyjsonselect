from nose.tools import *

import glob
import json
import sys

import cli


def test_all():
    specs = glob.glob('tests/*.spec')
    for spec in specs:
        args = json.load(open(spec))
        expected = json.load(open(spec.replace('.spec', '.out.json')))
        actual = cli.run(args)
        eq_(expected, actual)
