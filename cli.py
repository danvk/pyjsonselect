#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import sys
import time
from collections import OrderedDict

import jsonselect

DEBUG = False

UNSPECIFIED = 0
KEEP = 1
DELETE = 2


def selector_to_ids(selector, obj, mode):
    def bail_on_match(obj, matches):
        return matches

    bail_fn = None
    if mode == DELETE:
        # There's no point in continuing a search below a node which will be
        # marked for deletion.
        bail_fn = bail_on_match

    matches = jsonselect.match(selector, obj, bailout_fn=bail_fn)
    return [id(node) for node in matches]


def filter_object(obj, marks, presumption=DELETE):
    '''Filter down obj based on marks, presuming keys should be kept/deleted.

    Args:
        obj: The object to be filtered. Filtering is done in-place.
        marks: An object mapping id(obj) --> {DELETE,KEEP}
               These values apply to the entire subtree, unless inverted.
        presumption: The default action to take on all keys.
    '''
    if isinstance(obj, list):
        keys = reversed(range(0, len(obj)))
    else:
        keys = obj.keys()

    for k in keys:
        v = obj[k]
        m = marks.get(id(v), UNSPECIFIED)
        if m == DELETE:
            del obj[k]  # an explicit deletion is irreversible.
        elif m == KEEP or presumption==KEEP:
            # keep descending, in case there are nodes we should delete.
            if isinstance(v, list) or isinstance(v, dict):
                filter_object(v, marks, presumption=KEEP)
        elif m == UNSPECIFIED:
            # ... and presumption == DELETE
            if isinstance(v, list) or isinstance(v, dict):
                filter_object(v, marks, presumption=DELETE)
                if len(v) == 0:
                    del obj[k]
            else:
                del obj[k]


def usage():
    print '''%s [selector] [-v exclude_selector]

...
'''


class Timer(object):
    def __init__(self):
        '''Utility for logging timing info. Does nothing if DEBUG=False.'''
        self._start_time_ms_ = 1000 * time.time()
        self._last_time_ms_ = self._start_time_ms_
        self.log('Start')

    def log(self, statement):
        '''Write statement to stderr with timing info in DEBUG mode.'''
        global DEBUG
        time_ms = 1000 * time.time()
        if DEBUG:
            total_time_ms = time_ms - self._start_time_ms_
            lap_time_ms = time_ms - self._last_time_ms_
            sys.stderr.write('%6.f (%6.f ms) %s\n' % (
                total_time_ms, lap_time_ms, statement))
        self._last_time_ms_ = time_ms


def maybe_round(f):
    if round(f) == f:
        return '%d' % f
    else:
        return repr(f)

timer = Timer()

def run(args):
    global DEBUG
    path = args.pop()  # TODO: allow stdin
    actions = args

    if actions and actions[0] == '--debug':
        DEBUG = True
        del actions[0]

    timer.log('Loading JSON...')
    obj = json.load(open(path), object_pairs_hook=OrderedDict)
    timer.log('done loading JSON')
    while actions:
        action = actions[0]
        del actions[0]
        mode = KEEP
        presumption = DELETE
        if action == '-v':
            mode = DELETE
            action = actions[0]
            presumption = KEEP
            del actions[0]
        if action == '.':
            continue

        timer.log('Applying selector: %s' % action)
        marks = {k: mode for k in selector_to_ids(action, obj, mode)}
        timer.log('done applying selector')
        timer.log('filtering object...')
        filter_object(obj, marks, presumption=presumption)
        timer.log('done filtering')

    # Note: it's unclear whether rounding these floats is a good idea, but it's
    # what jq does, so we do it too to simplify comparisons.
    save = json.encoder.FLOAT_REPR
    json.encoder.FLOAT_REPR = maybe_round
    r = json.dumps(obj, indent=2, separators=(',', ': '), ensure_ascii=False) + '\n'
    json.encoder.FLOAT_REPR = save
    return r


if __name__ == '__main__':
    print run(sys.argv[1:]).encode('utf8'),
    timer.log('done printing')
