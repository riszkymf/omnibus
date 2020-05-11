import os
import sys
import string
import json
from .util import generate_respons, convert


def safe_to_json(in_obj):
    """ Safely get dict from object if present for json dumping """
    if isinstance(in_obj, bytes):
        return convert(in_obj)
    if hasattr(in_obj, "__dict__"):
        return in_obj.__dict__
    try:
        return str(in_obj)
    except:
        return repr(in_obj)


def flatten_dictionaries(input):
    output = dict()
    try:
        if isinstance(input, list):
            for map in input:
                output.update(map)
        else:  # Not a list of dictionaries
            output = input
    except Exception as e:
        return generate_respons(False, None, str(e))
    else:
        return output

def lowercase_keys(input_dict):
    if not isinstance(input_dict, dict):
        return False
    safe = dict()
    for key, value in input_dict.items():
        safe[str(key).lower()] = value
    return safe


def safe_to_bool(input):
    """ Safely convert user input to a boolean, throwing exception if not boolean or boolean-appropriate string
      For flexibility, we allow case insensitive string matching to false/true values
      If it's not a boolean or string that matches 'false' or 'true' when ignoring case, throws an exception """
    if isinstance(input, bool):
        return input
    elif isinstance(input, str) and input.lower() == u"false":
        return False
    elif isinstance(input, str) and input.lower() == u"true":
        return True
    else:
        raise TypeError("Input Object is not a boolean or string form of boolean!")


def safe_substitute_unicode_template(templated_string, variable_map):
    return string.Template(templated_string).safe_substitute(variable_map)


def encode_unicode_bytes(my_string):
    if not isinstance(my_string, str):
        my_string = convert(my_string)
    if isinstance(my_string, str):
        return my_string.encode('utf8')


def convert_to_dict(data):
    """Conver data to dictionary, if json not valid throw error . Tuple must be in (key,value) format"""
    if isinstance(data,dict):
        return data
    elif isinstance(data,str):
        try:
            return json.loads(data)
        except:
            raise ValueError("String is not a valid JSON")
    elif isinstance(data,tuple):
        retdat = dict()
        retdat[data[0]] = data[1]
        return retdat
    elif isinstance(data,list) and isinstance(data[0],tuple):
        retdat = dict()
        for key,value in data:
            retdat[key] = value
        return retdat
    else:
        raise ValueError("{} must be in JSON, tuples or list of tuples".format(data))

