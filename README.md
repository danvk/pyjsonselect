[![Build Status](https://travis-ci.org/danvk/pyjsonselect.svg?branch=master)](https://travis-ci.org/danvk/pyjsonselect) [![Coverage Status](https://coveralls.io/repos/danvk/pyjsonselect/badge.svg?branch=master)](https://coveralls.io/r/danvk/pyjsonselect?branch=master)

pyjsonselect
------------

A fully-conformant implementation of the [JSONSelect](http://jsonselect.org/)
standard in Python.

To install:

    pip install pyjsonselect

To use:

```python
import jsonselect

# prints 1, 2
for v in jsonselect.match('.foo', {'foo': 1, 'bar': {'foo': 2}}):
    print v
```

To run the tests:

```bash
git submodule update --init  # load conformance tests
pip install nose
nosetests
```
