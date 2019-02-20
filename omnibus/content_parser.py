import os
import sys
import json
from omnibus import generator
from omnibus import parsing
from omnibus import util
from omnibus import binding

class TestConfig:
	""" Test Set Configuration """
	retries = 0
	print_bodies = False
	print_headers = False
	variable_binds = False
	generator = False
	scope = None
	url = None


	def __str__(self):
		return json.dumps(self, default=safe_to_json)






def parse_file(test_structure, test_files=set() content, working_directory=None, vars=None, global_url=None):
	"""" Parse test content from single file """

	tests_config = TestConfig()



	if working_directory is None:
		working_directory = os.path.abspath(os.getcwd())

	if vars and isinstance(vars,dict):
		test_config.variable_binds = vars

	for node in test_structure:
		if isinstance(node,dict):
			node = parsing.lowercase_keys(node)['data']
			node = node['data']
			for key in node:
				if key == 'config' or key == 'configuration':
					test_config = parse_configuration(
						node[key], base_config=test_config)
	



def parse_configuration(node, base_config=None):
	""" Parse yaml configuration as information """
	test_config = base_config
	if not test_config:
		test_config = TestConfig()

	node = parsing.lowercase_keys(parsing.flatten_dictionaries(node)['data'])['data']

	for key,value in node.items():
		if key == 'url':
			test_config.url = str(value)
		elif key == 'scope':
			test_config.scope = str(value)
		elif key == 'variable_binds':
			if not test_config.variable_binds :
				test_config.variable_binds = dict()
			temp = dict()
			for row in value:
				if row['type'].lower() == 'int' or row['type'].lower() == 'integer':
					temp.update({row['name'] : int(row['value'])})
				elif row['type'].lower() == 'str' or row['type'].lower()=='string':
					temp.update({row['name'] : str(row['value'])})
			test_config.variable_binds.update(temp)
		elif key == 'generator':
			flat = parsing.flatten_dictionaries(value)
			gen_map = dict()
			for generator_name, generator_config in flat.items():
				gen = generator.parse_generator(generator_config)
				gen_map[str(generator_name)]= gen
	
	return test_config


def safe_to_json(in_obj):
    """ Safely get dict from object if present for json dumping """
    if isinstance(in_obj, bytearray):
        return str(in_obj)
    if hasattr(in_obj, '__dict__'):
        return in_obj.__dict__
    try:
        return str(in_obj)
    except:
        return repr(in_obj)