from omnibus.libs.content_parser import *
import os
import requests
from omnibus.libs.binding import Context
from omnibus.libs import util



# base_url = 'http://127.0.0.1:6968/'
# test_file = ['omnibus/test_copy.yml']
# test_structure = list()
# paths = list()
# for i in test_file:
#     test_structure.append(util.load_yaml(i))
#     paths.append(os.path.dirname(i))

# for t,p,f in zip(test_structure,paths,test_file):
#     var = {"mock_zone": 'test.com'}
#     tests = parse_file(test_structure,test_file,vars=var,global_url=base_url)
#     res = run_testsets(tests)



from omnibus.libs.content_parser import *
import os
import requests
from omnibus.libs.binding import Context
from omnibus.libs import util
base_url = 'http://127.0.0.1:6968/'
test_file = ['tests/test_ttl.yml']
test_file = test_file[0]
test_structure = util.load_yaml(test_file)
var = {"mock_zone": 'test.com'}
tests = parse_file(test_structure,test_file)

result = run_testsets(tests)

from omnibus.libs.util import *
import os
cwd = os.getcwd()
path = os.path.join(cwd,'tests')
ignore = 'tests/ignorejuga/test_4.yml'
ignore = os.path.join(cwd,ignore)
ignore = [ignore]
get_all(path,ignore)
