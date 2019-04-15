import sys
import pytest

sys.path.append('/home/mfriszky/worksworksworks/branch-sandbox/RESTKnot/API/omnibus/omnibus')
from omnibus.libs.binding import *

def count_gen():
    val = 1
    while(True):
        yield val
        val += 1

class TestBinding():

    def test_variables(self):

        context = Context()
        assert context.get_value('foo') is None
        assert context.mod_count == 0

        context.bind_variable('foo', 'bar')
        assert context.get_value('foo') is 'bar'
        assert context.get_values()['foo'] is 'bar'
        assert context.mod_count == 1

        context.bind_variable('foo','bar2')
        assert context.get_value('foo') is 'bar2'
        assert context.mod_count == 2

    
    def test_generator(self):
        context = Context()
        assert len(context.get_generators()) == 0
        
        my_gen = count_gen()
        context.add_generator('gen', my_gen)

        assert len(context.get_generators()) == 1
        assert 'gen' in context.get_generators()
        assert context.get_generator('gen') is not None

    def test_generator_bind(self):
        context = Context()
        assert len(context.get_generators()) == 0
        my_gen = count_gen()
        context.add_generator('gen',my_gen)

        context.bind_generator_next('foo','gen')

        assert context.mod_count is 1
        assert context.get_value('foo') == 1
        assert next(context.get_generator('gen')) == 2
        assert next(my_gen) == 3

    def test_mixing_binds(self):
        context = Context()
        context.add_generator('gen', count_gen())
        context.bind_variable('foo','100')

        assert context.mod_count == 1

        context.bind_generator_next('foo','gen')
        assert context.get_value('foo') == 1
        assert context.mod_count == 2