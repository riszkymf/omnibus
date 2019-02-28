from omnibus.content_parser import *
import os
import requests
from omnibus.binding import Context



base_url = 'http://127.0.0.1:6968/'
test_file = 'test_rest.yml'
test_structure = util.load_yaml(test_file)
path = os.path.dirname(test_file)
tests = parse_file(test_structure,test_file,path,vars=None,global_url=base_url)
res = run_testsets(tests)