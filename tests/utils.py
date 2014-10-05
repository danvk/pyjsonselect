import json
from collections import OrderedDict

def jsonLoadOrdered(string):
    '''Like json.loads, but puts k/v pairs in an OrderedDict.'''
    return json.loads(string, object_pairs_hook=OrderedDict)
