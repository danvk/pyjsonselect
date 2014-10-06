#!/usr/bin/env python

import sys
import json

import jsonselectjs

import gflags
FLAGS = gflags.FLAGS


def selector_to_ids(selector, obj):
    return [id(node) for node in jsonselectjs.match(selector, obj)]


UNSPECIFIED = 0
KEEP = 1
DELETE = 2

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


def run(args):
    path = args.pop()  # TODO: allow stdin
    actions = args

    obj = json.load(open(path))
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

        marks = {k: mode for k in selector_to_ids(action, obj)}
        filter_object(obj, marks, presumption=presumption)

    return obj


if __name__ == '__main__':
    obj = run(sys.argv[1:])
    # TODO: preserve the input ordering of keys
    print json.dumps(obj, indent=2, sort_keys=True)
