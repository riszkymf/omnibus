import pytest
import sys
import os

sys.path.append('/home/mfriszky/worksworksworks/branch-sandbox/RESTKnot/API/omnibus/omnibus')
from omnibus.libs import validators
from omnibus.libs.validators import register_extractor,AbstractExtractor,AbstractValidator,register_validator,ComparatorValidator,register_comparator
from omnibus.libs.binding import Context

class TestValidators():

    def test_failure_obj(self):
        myfailure = validators.Failure()
        assert not myfailure

    def test_contains_opereators(self):
        cont_func = validators.COMPARATORS['contains']
        cont_by_func = validators.COMPARATORS['contained_by']

        assert cont_func('abagooberab23', 'goob')
        assert cont_by_func('goob', 'abagooberab23')

        array = ['math',1,None,u'lest']
        assert cont_func(array,1)
        assert cont_func(array,None)
        assert cont_by_func(None,array)

        assert not cont_func(None,'pow')
        assert not cont_by_func('test',None)

    def test_type_comparator(self):

        type_test = validators.COMPARATORS['type']
        hasfailed = False
        instances = {
            'string': 'goober',
            'int': 1,
            'float': 0.5,
            'boolean': False,
            'number': 1,
            'array': [4, 'val'],
            'list': ['my', 1, None],
            'none': None,
            'null': None,
            'scalar': 4.0,
            'collection': ['collection', 1, None],
            'dict': {1: 'ring', 4: 1, 'gollum': 'smeagol'}
        }


        for mytype, myinstance in instances.items():
            try :
                assert type_test(myinstance,mytype)
            except Exception:
                print('Failure in {} ===> {}'.format(myinstance,mytype))
                hasfailed = True

    def test_type_comparator_failures(self):
        type_test = validators.COMPARATORS['type']
        hasfailed = False

        failing_instances = {
            'string': 1,
            'int': {'nope': 3},
            'float': 3,
            'boolean': None,
            'number': 'lolz',
            'array': False,
            'list': 'string here',
            'none': 4,
            'scalar': {'key': 'val'},
            'collection': 'string',
            'dict': [1, 2, 3]
        }

        for mytype, myinstance in failing_instances.items():
            try:
                assert not type_test(myinstance, mytype)
            except :
                print('Type test operator passed where should fail for type {0} and value {1}'.format(
                    mytype, myinstance))

    def test_type_comparator_specialcases(self):
        type_test = validators.COMPARATORS['type']
        assert type_test('string', 'scALar')
        assert type_test(None, 'scalar')

        with pytest.raises(Exception):
            type_test(3,'doesnotexist')

    def test_safe_length(self):
        assert validators.safe_length('s') == 1
        assert validators.safe_length(['text',2]) == 2
        assert validators.safe_length({'key' : 'val', '1' : 2}) == 2
        assert validators.safe_length(False) == -1
        assert validators.safe_length(None) == -1

    def test_validatortest_exists(self):
        func = validators.VALIDATOR_TESTS['exists']
        
        assert func('blah')
        assert func(0)
        assert func('False')
        assert func(False)
        assert not func(None)

    def test_validatortest_not_exists(self):
        func = validators.VALIDATOR_TESTS['not_exists']
        assert not func('blah')
        assert not func(0)
        assert not func('False')
        assert func(None)

    def test_dict_query(self):
        """ Test actual query logic """
        mydict = {'key': {'val': 3}}
        query = 'key.val'
        val = validators.MiniJsonExtractor.query_dictionary(query, mydict)
        assert 3 == val

        array = [1, 2, 3]
        mydict = {'key': {'val': array}}
        val = validators.MiniJsonExtractor.query_dictionary(query, mydict)
        assert array == val

        mydict = {'key': {'v': 'pi'}}
        val = validators.MiniJsonExtractor.query_dictionary(query, mydict)
        assert val == None

        # Array test
        query = 'key.val.1'
        mydict = {'key': {'val': array}}
        val = validators.MiniJsonExtractor.query_dictionary(query, mydict)
        assert array[1] == val

        # Error cases
        query = 'key.val.5'
        mydict = {'key': {'val': array}}
        val = validators.MiniJsonExtractor.query_dictionary(query, mydict)
        assert None == val

        query = 'key.val.pi'
        mydict = {'key': {'val': array}}
        val = validators.MiniJsonExtractor.query_dictionary(query, mydict)
        assert val == None

        # Return the first object?
        query = 'key.0'
        mydict = {'key': {'val': array}}
        val = validators.MiniJsonExtractor.query_dictionary(query, mydict)
        assert val == None

        # Mix array array and dictionary
        mydict = [{'key': 'val'}]
        query = '0.key'
        val = validators.MiniJsonExtractor.query_dictionary(query, mydict)
        assert val == 'val'

    def test_jsonpathmini_unicode(self):
        myjson = u'{"myVals": [0, 1.0, "😽"], "my😽":"value"}'

        query_normal = validators.MiniJsonExtractor.parse('myVals.2')
        assert u'😽' == query_normal.extract(body=myjson)

        query_unicode = validators.MiniJsonExtractor.parse(u'my😽')
        assert 'value' == query_unicode.extract(body=myjson)

    def test_jsonpathmini_wholeobject(self):
        """ Verify that the whole Json object can be returned by delimiter queries """

        myobj = {'key': {'val': 3}}
        query = ''
        val = validators.MiniJsonExtractor.query_dictionary(query, myobj)
        assert myobj == val

        myobj = [{'key': 'val'}, 3.0, {1: 'val'}]
        val = validators.MiniJsonExtractor.query_dictionary(query, myobj)
        assert myobj == val

        query = '.'
        val = validators.MiniJsonExtractor.query_dictionary(query, myobj)
        assert myobj == val

        query = '..'
        val = validators.MiniJsonExtractor.query_dictionary(query, myobj)
        assert myobj == val


    def test_parse_extractor_minijson(self):
        config = 'key.val'
        extractor = validators.MiniJsonExtractor.parse(config)
        myjson = '{"key": {"val": 3}}'
        context = Context()
        context.bind_variable('node', 'val')

        extracted = extractor.extract(body=myjson)
        assert 3 == extracted
        assert extractor.extract(body=myjson, context=context) == extracted

        with pytest.raises(ValueError):
            val = extractor.extract(body='[31{]')
        

        # Templating
        config = {'template': 'key.$node'}
        extract = validators.MiniJsonExtractor.parse(config)
        assert 3 == extract.extract(myjson, context=context)

    def test_header_extractor(self):
        query = 'content-type'
        extractor = validators.HeaderExtractor.parse(query)
        headers = [('content-type', 'application/json')]
        extracted = extractor.extract(body='blahblah', headers=headers)
        assert headers[0][1] == extracted

        # Test case-insensitivity
        query = 'content-Type'
        extractor = validators.HeaderExtractor.parse(query)
        extracted = extractor.extract(body='blahblah', headers=headers)
        assert headers[0][1] == extracted

        # Throws exception if invalid header
        with pytest.raises(ValueError):
            headers = [('foo', 'bar')]
            extracted = extractor.extract(body='blahblah', headers=headers)


    def test_header_extractor_duplicatekeys(self):
        # Test for handling of multiple headders
        query = 'content-Type'
        headers = [('content-type', 'application/json'),
                   ('content-type', 'x-json-special')]
        extractor = validators.HeaderExtractor.parse(query)
        extracted = extractor.extract(body='blahblah', headers=headers)
        
        assert (isinstance(extracted, list))
        assert headers[0][1] == extracted[0]
        assert headers[1][1] == extracted[1]


    def test_parse_header_extractor(self):
        query = 'content-type'
        extractor = validators.parse_extractor('header', query)
        assert (isinstance(extractor, validators.HeaderExtractor))
        assert (extractor.is_header_extractor)
        assert not (extractor.is_body_extractor)

    def test_raw_body_extractor(self):
        query = ''
        extractor = validators.parse_extractor('raw_body', None)
        extractor = validators.parse_extractor('raw_body', query)
        assert (isinstance(extractor, validators.RawBodyExtractor))
        assert (extractor.is_body_extractor)
        assert not (extractor.is_header_extractor)

        bod = u'j1j21io312j3'
        val = extractor.extract(body=bod, headers='')
        assert bod == val

        bod = b'j1j21io312j3'
        val = extractor.extract(body=bod, headers='')
        assert bod == val


    def test_abstract_extractor_parse(self):
        """ Test parsing a basic abstract extractor """
        ext = validators.AbstractExtractor()
        ext = validators.AbstractExtractor.configure_base('val', ext)
        assert ext.query == 'val'
        assert not ext.is_templated

        validators.AbstractExtractor.configure_base({'template': '$var'}, ext)
        assert ext.is_templated
        assert ext.query == '$var'

    def test_abstract_extractor_string(self):
        """ Test abstract extractor to_string method """
        ext = validators.AbstractExtractor()
        ext.is_templated = True
        ext.is_header_extractor = True
        ext.is_body_extractor = True
        ext.query = 'gooblyglah'
        ext.extractor_type = 'bleh'
        ext.args = {'cheesy': 'poofs'}

        expected = "Extractor type: {0}, query: {1}, is_templated: {2}, args: {3}".format(
            ext.extractor_type, ext.query, ext.is_templated, ext.args)
        assert expected == str(ext)

    def test_abstract_extractor_templating(self):
        """ Test that abstract extractors template the query """
        ext = validators.AbstractExtractor()
        ext.query = '$val.vee'
        ext.is_templated = True
        context = Context()
        context.bind_variable('val', 'foo')
        assert '$val.vee' == ext.templated_query()
        assert 'foo.vee' == ext.templated_query(context=context)

        ext.is_templated = False
        assert '$val.vee' == ext.templated_query(context=context)

    def test_abstract_extractor_readableconfig(self):
        """ Test human-readable extractor config string output """
        config = 'key.val'
        extractor = validators.parse_extractor('jsonpath_mini', config)
        expected_string = 'Extractor Type: jsonpath_mini,  Query: "key.val", Templated?: False'
        assert expected_string == extractor.get_readable_config()

        # Check empty context & args uses okay
        context = Context()
        assert expected_string == extractor.get_readable_config(context=context)
        context.bind_variable('foo', 'bar')
        assert expected_string == extractor.get_readable_config(context=context)
        extractor.args = dict()
        assert expected_string == extractor.get_readable_config(context=context)

        # Check args output is handled correctly
        extractor.args = {'caseSensitive': True}
        assert (expected_string + ", Args: " + str(extractor.args)) == extractor.get_readable_config(context=context)

        # Check template handling is okay
        config = {'template': 'key.$templated'}
        context.bind_variable('templated', 'val')
        extractor = validators.parse_extractor('jsonpath_mini', config)
        expected_string = 'Extractor Type: jsonpath_mini,  Query: "key.val", Templated?: True'
        assert expected_string == extractor.get_readable_config(context=context)


    def test_parse_extractor(self):
        """ Test parsing an extractor using the registry """
        config = 'key.val'
        myjson = '{"key": {"val": 3}}'
        extractor = validators.parse_extractor('jsonpath_mini', config)
        assert isinstance(extractor, validators.AbstractExtractor)
        assert 3 == extractor.extract(body=myjson)

    def test_get_extractor(self):
        config = {
            'jsonpath_mini': 'key.val',
            'comparator': 'eq',
            'expected': 3
        }
        extractor = validators._get_extractor(config)
        myjson = u'{"key": {"val": 3}}'
        extracted = extractor.extract(body=myjson)
        assert 3 == extracted

        myjson = b'{"key": {"val": 3}}'
        extracted = extractor.extract(body=myjson)
        assert 3 == extracted

    def test_parse_validator(self):
        """ Test basic parsing using registry """
        config = {
            'jsonpath_mini': 'key.val',
            'comparator': 'eq',
            'expected': 3
        }
        validator = validators.parse_validator('comparator', config)
        myjson = '{"key": {"val": 3}}'
        comp = validator.validate(body=myjson)

        # Try it with templating
        config['jsonpath_mini'] = {'template': 'key.$node'}
        validator = validators.parse_validator('comparator', config)
        context = Context()
        context.bind_variable('node', 'val')
        comp = validator.validate(myjson, context=context)

    def test_parse_validator_nocomparator(self):
        """ Test that comparator validator with no comparator defaults to eq """
        config = {
            'jsonpath_mini': 'key.val',
            'expected': 3
        }
        validator = validators.parse_validator('assertEqual', config)
        assert 'eq' == validator.comparator_name
        assert validators.COMPARATORS['eq'] == validator.comparator

    def test_validator_compare_eq(self):
        """ Basic test of the equality validator"""
        config = {
            'jsonpath_mini': 'key.val',
            'comparator': 'eq',
            'expected': 3
        }
        comp_validator = validators.ComparatorValidator.parse(config)
        myjson_pass = '{"id": 3, "key": {"val": 3}}'
        myjson_fail = '{"id": 3, "key": {"val": 4}}'

        assert (comp_validator.validate(body=myjson_pass))
        assert not (comp_validator.validate(body=myjson_fail))

    def test_validator_unicode_comparison(self):
        """ Checks for implicit unicode -> byte conversion in testing """
        config = {
            'raw_body': '.',
            'comparator': 'contains',
            'expected': u'stuff'
        }
        comp_validator = validators.ComparatorValidator.parse(config)
        myjson_pass = b'i contain stuff because win'
        myjson_fail = b'i fail without it'
        assert (comp_validator.validate(body=myjson_pass))
        assert not (comp_validator.validate(body=myjson_fail))

        # Let's try this with unicode characters just for poops and giggles
        config = {
            'raw_body': '.',
            'comparator': 'contains',
            'expected': u'cat😽stuff'
        }
        myjson_pass = u'i contain cat😽stuff'.encode('utf-8')
        myjson_pass_unicode = u'i contain encoded cat😽stuff'
        assert (comp_validator.validate(body=myjson_pass))
        assert (comp_validator.validate(body=myjson_pass_unicode))

    def test_validator_compare_ne(self):
        """ Basic test of the inequality validator"""
        config = {
            'jsonpath_mini': 'key.val',
            'comparator': 'ne',
            'expected': 3
        }
        comp_validator = validators.ComparatorValidator.parse(config)
        myjson_pass = '{"id": 3, "key": {"val": 4}}'
        myjson_fail = '{"id": 3, "key": {"val": 3}}'

        assert (comp_validator.validate(body=myjson_pass))
        assert not (comp_validator.validate(body=myjson_fail))

    def test_validator_compare_not_equals(self):
        """ Basic test of the inequality validator alias"""
        config = {
            'jsonpath_mini': 'key.val',
            'comparator': 'not_equals',
            'expected': 3
        }
        comp_validator = validators.ComparatorValidator.parse(config)
        myjson_pass = '{"id": 3, "key": {"val": 4}}'
        myjson_fail = '{"id": 3, "key": {"val": 3}}'

        assert (comp_validator.validate(body=myjson_pass))
        assert not (comp_validator.validate(body=myjson_fail))


    def test_validator_comparator_templating(self):
        """ Try templating comparator validator """
        config = {
            'jsonpath_mini': {'template': 'key.$node'},
            'comparator': 'eq',
            'expected': 3
        }
        context = Context()
        context.bind_variable('node', 'val')
        myjson_pass = '{"id": 3, "key": {"val": 3}}'
        myjson_fail = '{"id": 3, "key": {"val": 4}}'
        comp = validators.ComparatorValidator.parse(config)

        assert (comp.validate(body=myjson_pass, context=context))
        assert not (comp.validate(body=myjson_fail, context=context))

        # Template expected
        config['expected'] = {'template': '$id'}
        context.bind_variable('id', 3)
        assert (comp.validate(body=myjson_pass, context=context))
        assert not (comp.validate(body=myjson_fail, context=context))

    def test_validator_comparator_extract(self):
        """ Try comparing two extract expressions """
        config = {
            'jsonpath_mini': 'key.val',
            'comparator': 'eq',
            'expected': {'jsonpath_mini': 'id'}
        }
        myjson_pass = '{"id": 3, "key": {"val": 3}}'
        myjson_fail = '{"id": 3, "key": {"val": 4}}'
        comp = validators.ComparatorValidator.parse(config)
        assert (comp.validate(body=myjson_pass))
        failure = comp.validate(body=myjson_fail)
        assert not (failure)

    def test_validator_error_responses(self):
        config = {
            'jsonpath_mini': 'key.val',
            'comparator': 'eq',
            'expected': 3
        }
        comp = validators.ComparatorValidator.parse(config)
        myjson_fail = '{"id": 3, "key": {"val": 4}}'
        failure = comp.validate(body=myjson_fail)

        # Test the validator failure object handling
        assert not (failure)
        assert failure.message == 'Comparison failed, evaluating eq(4, 3) returned False'
        assert failure.message == str(failure)
        assert failure.failure_type == validators.FAILURE_VALIDATOR_FAILED
        expected_details = 'Extractor: Extractor Type: jsonpath_mini,  Query: "key.val", Templated?: False'
        assert expected_details == failure.details
        print("Failure config: " + str(failure.details))
        assert comp == failure.validator

        failure = comp.validate(body='{"id": 3, "key": {"val": 4}')
        assert (isinstance(failure, validators.Failure))


    def test_parse_validator_jmespath_extracttest(self):
        config = {
            'jmespath': 'key.val',
            'test': 'exists'
        }
        myjson_pass = '{"id": 3, "key": {"val": 3}}'
        myjson_fail = '{"id": 3, "key": {"valley": "wide"}}'
        validator = validators.ExtractTestValidator.parse(config)

        validation_result = validator.validate(body=myjson_pass)
        assert (validation_result)

        validation_result = validator.validate(body=myjson_fail)
        assert not (validation_result)

        assert (isinstance(validation_result, validators.Failure))
        assert validation_result.message == "Extract and test validator failed on test: exists(None)"


    def test_parse_validator_jsonpath_mini_extracttest(self):
        """ Test parsing for jsonpath_mini extract test """
        config = {
            'jsonpath_mini': 'key.val',
            'test': 'exists'
        }
        myjson_pass = '{"id": 3, "key": {"val": 3}}'
        myjson_fail = '{"id": 3, "key": {"valley": "wide"}}'
        validator = validators.ExtractTestValidator.parse(config)
        validation_result = validator.validate(body=myjson_pass)
        assert (validation_result)

        validation_result = validator.validate(body=myjson_fail)
        assert not (validation_result)
        assert (isinstance(validation_result, validators.Failure))
        assert validation_result.message == "Extract and test validator failed on test: exists(None)"


    def test_register_extractor(self):

        fail_name = [7777,'comparator','test','expected','raw_body']
        success = 'midnight'

        for i in fail_name:
            with pytest.raises(Exception):
                register_extractor(i,TestBodyExtractor.parse)

        register_extractor(success,TestBodyExtractor)


    def test_register_comparator(self):
        fail_name = [3456,'regex']
        success = 'test_compare'

        def compare_but_fail(self):
            pass
        
        for i in fail_name:
            with pytest.raises(Exception):
                register_comparator(i,ComparatorValidator.parse)
        
        register_validator(success,compare_but_fail)





class TestBodyExtractor(AbstractExtractor):
    """ Extractor that returns the full request body """

    extractor_type = "test"
    is_header_extractor = False
    is_body_extractor = True

    def extract_internal(self, query=None, args=None, body=None, headers=None):
        return body

    @classmethod
    def parse(cls, config, extractor_base=None):
        # Doesn't take any real configuration
        base = TestBodyExtractor()
        return base
