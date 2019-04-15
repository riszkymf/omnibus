import pytest
import sys
import os
import string
import types

sys.path.append('/home/mfriszky/worksworksworks/branch-sandbox/RESTKnot/API/omnibus/omnibus')
from omnibus.libs.generator import *


class TestGenerator():

    def generator_basic_test(self, generator, value_test_function=None):
        assert isinstance(generator, types.GeneratorType)

        for x in range(0,100):
            val = next(generator)
            assert val is not None
            if value_test_function:
                try:
                    assert value_test_function(val) 
                except:
                   print('Test failed with value {}'.format(val))
    
    def generator_repeat_test(self,generator_input):
        val = next(generator_input)

        for x in range(0, 5):
            val2 = next(generator_input)
            assert val
            assert val != val2
            val = val2

    def test_factory_ids(self):
        f = generate_ids(1)()
        f2 = generate_ids(101)()
        f3 = generate_ids(1)()

        vals = [next(f), next(f)]
        vals2 = [next(f2), next(f2)]
        vals3 = [next(f3), next(f3)]

        assert vals[0] == 1
        assert vals[1] == 2

        assert vals2[0] == 101
        assert vals2[1] == 102

        assert vals3[0] == 1
        assert vals3[1] == 2

    def test_basic_ids(self):
        ids1 = generator_basic_ids()
        ids2 = generator_basic_ids()
        self.generator_repeat_test(ids1)
        self.generator_repeat_test(ids2)

        assert next(ids1) == next(ids2)

    def test_random_ids(self):
        gen = generator_random_int32()
        print(next(gen))
        self.generator_repeat_test(gen)

    def test_system_variables(self):
        variable = 'FOOBARBAZ'
        value = 'myTestVal'
        old_val = os.environ.get(variable)

        generator = factory_env_variable(variable)()
        assert next(generator) is None
        os.environ[variable] = value
        assert value == next(generator)
        assert next(generator) == os.path.expandvars('$' + variable)

        if old_val is not None:
            os.environ[variable] = old_val
        else:
            del os.environ[variable]

    def test_factory_text(self):
        charsets = [string.ascii_letters, string.digits, string.ascii_uppercase, string.hexdigits]
        for charset in charsets:
            for my_length in range(1,17):
                gen = factory_generate_text(
                    charset,my_length,my_length
                )()
                for x in range(0,10):
                    val = next(gen)
                    assert my_length == len(val)

    def test_factory_sequence(self):
        vals = [1]
        gen = factory_fixed_sequence(vals)()
        self.generator_basic_test(gen, lambda x: x in vals)

        vals = ['moobie', 'moby', 'moo']
        gen = factory_fixed_sequence(vals)()
        self.generator_basic_test(gen, lambda x: x in vals)

        vals = set(['a', 'b', 'c'])
        gen = factory_fixed_sequence(vals)()
        self.generator_basic_test(gen, lambda x: x in vals)

    def test_factory_choice(self):
        """ Tests linear sequences """
        vals = [1]
        gen = factory_choice_generator(vals)()
        self.generator_basic_test(gen, lambda x: x in vals)

        vals = ['moobie', 'moby', 'moo']
        gen = factory_choice_generator(vals)()
        self.generator_basic_test(gen, lambda x: x in vals)

        vals = set(['a', 'b', 'c'])
        gen = factory_choice_generator(vals)()
        self.generator_basic_test(gen, lambda x: x in vals)

    def test_parse_choice_generatpr(self):
        vals = ['moobie', 'moby', 'moo']
        config = {'type': 'choice',
                  'values': vals}
        gen = parse_generator(config)
        self.generator_basic_test(gen, lambda x: x in vals)

    def test_factory_text_multilength(self):
        """ Test that the random text generator can handle multiple lengths """
        gen = factory_generate_text(
            legal_characters='abcdefghij', min_length=1, max_length=100)()
        lengths = set()
        for x in range(0, 100):
            lengths.add(len(next(gen)))
        assert len(lengths) > 1

    def test_character_sets(self):
        """ Verify all charsets are valid """
        sets = CHARACTER_SETS
        for key, value in sets.items():
            assert value
    def test_parse_text_generator(self):
        """ Test the text generator parsing """
        config = dict()
        config['type'] = 'random_text'
        config['character_set'] = 'reallyINVALID'

        try:
            gen = parse_generator(config)
            self.fail(
                "Should never parse an invalid character_set successfully, but did!")
        except ValueError:
            pass

        # Test for character set handling
        for charset in CHARACTER_SETS:
            try:
                config['character_set'] = charset
                gen = parse_generator(config)
                myset = set(CHARACTER_SETS[charset])
                for x in range(0, 50):
                    val = next(gen)
                    assert (set(val).issubset(set(myset)))
            except Exception as e:
                print('Exception occurred with charset: ' + charset)
                raise e

        my_min = 1
        my_max = 10

        # Test for explicit character setting
        del config['character_set']
        temp_chars = 'ay78%&'
        config['characters'] = temp_chars
        gen = parse_generator(config)
        self.generator_basic_test(
            gen, value_test_function=lambda x: set(x).issubset(set(temp_chars)))

        # Test for length setting
        config['length'] = '3'
        gen = parse_generator(config)
        self.generator_basic_test(
            gen, value_test_function=lambda x: len(x) == 3)
        del config['length']

        # Test for explicit min/max length
        config['min_length'] = '9'
        config['max_length'] = 12
        gen = parse_generator(config)
        self.generator_basic_test(
            gen, value_test_function=lambda x: len(x) >= 9 and len(x) <= 12)

    def test_parse_basic(self):
        """ Test basic parsing, simple cases that should succeed or throw known errors """
        config = {'type': 'unsupported'}

        try:
            gen = parse_generator(config)
            self.fail(
                "Expected failure due to invalid generator type, did not emit it")
        except ValueError:
            pass

        # Try creating a random_int generator
        config['type'] = 'random_int'
        gen = parse_generator(config)
        self.generator_basic_test(
            gen, value_test_function=lambda x: isinstance(x, int))
        self.generator_repeat_test(gen)

        # Sample variable
        os.environ['SAMPLEVAR'] = 'goober'

        config['type'] = 'env_variable'
        config['variable_name'] = 'SAMPLEVAR'
        gen = parse_generator(config)
        self.generator_basic_test(gen)
        del config['variable_name']

        config['type'] = 'env_string'
        config['string'] = '$SAMPLEVAR'
        gen = parse_generator(config)
        self.generator_basic_test(gen)
        del config['string']

        config['type'] = 'number_sequence'
        config['start'] = '1'
        config['increment'] = '10'
        gen = parse_generator(config)
        assert next(gen) == 1
        assert next(gen) == 11
        self.generator_basic_test(gen)
        del config['type']

    