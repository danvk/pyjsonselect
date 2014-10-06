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
for v in jsonselect.match('.foo', {'foo': 1, 'bar': {'foo': 2}):
    print v
```

To run the tests:

   pip install nose
   nosetests