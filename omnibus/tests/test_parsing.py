import sys
import pytest
import json

sys.path.append('/home/mfriszky/worksworksworks/branch-sandbox/RESTKnot/API/omnibus/omnibus')

from omnibus.libs.parsing import *

class TestParsing():

    def test_encode_unicode_bytes(self):
        val = 8
        unicoded = u'指事字'
        byteform = b'\xe6\x8c\x87\xe4\xba\x8b\xe5\xad\x97'
        num = 156
        assert byteform == encode_unicode_bytes(unicoded)
        assert b'156' == encode_unicode_bytes(num)
        assert byteform == encode_unicode_bytes(byteform)

    def test_flatten(self):
        """ Test flattening of lists of dictionaries to single dictionaries """

        # Test happy path: list of single-item dictionaries in
        array = [{"url": "/cheese"}, {"method": "POST"}]
        expected = {"url": "/cheese", "method": "POST"}
        output = flatten_dictionaries(array)['data']
        assert isinstance(output, dict)
        # Test that expected output matches actual
        assert len(set(output.items())) == len(set(expected.items()))

        # Test dictionary input
        array = {"url": "/cheese", "method": "POST"}
        expected = {"url": "/cheese", "method": "POST"}
        output = flatten_dictionaries(array)['data']
        assert (isinstance(output, dict))
        # Test that expected output matches actual
        assert (len(set(output.items()) ^ set(expected.items())) == 0)

        # Test empty list input
        array = []
        expected = {}
        output = flatten_dictionaries(array)['data']
        assert (isinstance(output, dict))
        # Test that expected output matches actual
        assert (len(set(output.items()) ^ set(expected.items()))) == False

        # Test empty dictionary input
        array = {}
        expected = {}
        output = flatten_dictionaries(array)['data']
        assert (isinstance(output, dict))
        # Test that expected output matches actual
        assert (len(set(output.items()) ^ set(expected.items()))) == False

        # Test mixed-size input dictionaries
        array = [{"url": "/cheese"}, {"method": "POST", "foo": "bar"}]
        expected = {"url": "/cheese", "method": "POST", "foo": "bar"}
        output = flatten_dictionaries(array)['data']
        assert (isinstance(output, dict))
        # Test that expected output matches actual
        assert (len(set(output.items()) ^ set(expected.items()))) == False

    def test_safe_boolean(self):
        """ Test safe conversion to boolean """
        assert (safe_to_bool(False)) == False
        assert (safe_to_bool(True))
        assert (safe_to_bool('True'))
        assert (safe_to_bool('true'))
        assert (safe_to_bool('truE'))
        assert (safe_to_bool('false')) == False

    def test_safe_to_json(self):

        assert u'dadsace212' == safe_to_json(u'dadsace212')
        assert u'5.2' == safe_to_json(5.2)
        assert '3233' == safe_to_json(b'3233')
        class Special(object):
            bal = 5.3
            test = 'stuffing'

            def __init__(self):
                self.newval = 'cherries'
        
        assert {'newval' : 'cherries'} == safe_to_json(Special())


    def test_dict_conversion(self):

        d_dict = { "first_name" : "VM" , "last_name" : "Varga" }
        d_json = json.dumps(d_dict)
        d_tuples_list = list(d_dict.items())
        d_fail = list(d_dict.keys())
        d_tuple = d_tuples_list[0]

        result = convert_to_dict(d_dict)
        assert d_dict == result

        result = convert_to_dict(d_json)
        assert d_dict == result

        result = convert_to_dict(d_tuples_list)
        assert d_dict == result

        result = convert_to_dict(d_tuple)
        assert result['first_name'] == "VM"

        with pytest.raises(Exception):
            result = convert_to_dict(d_fail)
        with pytest.raises(Exception):
            result = convert_to_dict("FAIL")




