import os
import sys
import string

def flatten_dictionaries(input):
	output = dict()
	try:
		if isinstance(input, list):
			for map in input:
				output.update(map)
		else:  # Not a list of dictionaries
			output = input
	except Exception as (e):
		return generate_respons(False,None,str(e))
	else :
		return generate_respons(True,output)


def lowercase_keys(input_dict):
    if not isinstance(input_dict, dict):
        return generate_respons(False,input_dict,"Data is not dict type")
    safe = dict()
    for key, value in input_dict.items():
        safe[str(key).lower()] = value
    return generate_respons(True,safe)


def safe_to_bool(input):
    """ Safely convert user input to a boolean, throwing exception if not boolean or boolean-appropriate string
      For flexibility, we allow case insensitive string matching to false/true values
      If it's not a boolean or string that matches 'false' or 'true' when ignoring case, throws an exception """
    if isinstance(input, bool):
        return input
    elif isinstance(input, basestring) and input.lower() == u'false':
        return False
    elif isinstance(input, basestring) and input.lower() == u'true':
        return True
    else:
        raise TypeError(
            'Input Object is not a boolean or string form of boolean!')