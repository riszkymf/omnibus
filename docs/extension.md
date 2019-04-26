# Extensions

Omnibus let you write your own extractor, validator and generator with extensions. 

### Example of Extension :

```python
from omnibus.libs import validators
from omnibus.libs import generator

def parse_generator_doubling(config):

    start = 1
    if 'start' in config:
        start = int(config['start'])

    # We cannot simply use start as the variable, because of scoping limitations
    def generator():
        val = start
        while(True):
            yield val
            val = val*2
    return generator()

GENERATORS = {'doubling': parse_generator_doubling}

```

**NOTE THAT EXTENSIONS NEED TO BE IMPORTED WHEN YOU ARE EXECUTING OMNIBUS TO WORK**


### Steps in writing your own extension

For extensions to work, it need function to be called and it need to be executed during invocation.
For full example on extension, see [example files](example/test_extensions.py)

