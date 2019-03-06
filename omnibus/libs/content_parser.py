import os
import sys
import threading
import json
import requests
import logging
import traceback

from omnibus.libs import generator
from omnibus.libs import parsing
from omnibus.libs import util
from omnibus.libs import binding
from omnibus.libs import validators
from omnibus.libs.tests import Test, DEFAULT_TIMEOUT
from omnibus.libs.binding import Context
from omnibus.libs.validators import Failure

DIR_LOCK = threading.RLock()

LOGGING_LEVELS = {"debug" : logging.DEBUG,
                  "info" : logging.INFO,
                  "warning": logging.WARNING,
                  "error": logging.ERROR,
                  "critical": logging.CRITICAL}
logging.basicConfig(format='%(levelname)s:%(message)s')
logger = logging.getLogger('omnibus')

class cd:
  """Context manager for changing the current working directory """
  
  def __init__(self,newPath):
    self.newPath = newPath

  def __enter__(self):
    if self.newPath:
      DIR_LOCK.acquire()
      self.savedPath = os.getcwd()
      os.chdir(self.newPath)

  def __exit__(self,etype,value,traceback):
    if self.newPath:
      os.chdir(self.savedPath)
      DIR_LOCK.release()

class TestConfig:
  """ Test Set Configuration """
  timeout = DEFAULT_TIMEOUT
  retries = 0
  print_bodies = True
  print_headers = False
  variable_binds = False
  generators = False
  scope = None
  url = None
  verbose = False
  ssl_insecure = False
  stream = False
  cert = None
  interactive = False
  skip_term_colors = False


  def __str__(self):
    return json.dumps(self, default=safe_to_json)

class TestSet:
  """ Container for test sets """
  tests = list()
  config = TestConfig()

  def __init__(self):
    self.config = TestConfig()
    self.tests = list()

  def __str__(self):
    return json.dumps(self, default=self_to_json)
  


def parse_file(test_structure, test_files=set(), working_directory=None, vars=None, global_url=None):
  """" Parse test content from single file """

  test_out = list()
  test_config = TestConfig()
  tests_out = list()
  testsets = list()


  if working_directory is None:
    working_directory = os.path.abspath(os.getcwd())

  if vars and isinstance(vars,dict):
    test_config.variable_binds = vars

  for node in test_structure:
    if isinstance(node,dict):
      node = parsing.lowercase_keys(node)
      node = node['data']
      for key in node:
        if key == 'config' or key == 'configuration':
          if 'url' in parsing.flatten_dictionaries(node[key])['data']:
            global_url = parsing.flatten_dictionaries(node[key])['data']['url']
          test_config = parse_configuration(
            node[key], base_config=test_config)
        elif key == 'test':
          with cd(working_directory):
            child = node[key]
            mytest = Test.parse_test(global_url, child)
            tests_out.append(mytest)

  testset = TestSet()
  testset.tests = tests_out
  testset.config = test_config
  testsets.append(testset)
  return testsets
            

class TestResponse:
  """ Encapsulates everything about a test response """
  test = None  # Test run
  response_code = None

  body = None  # Response body, if tracked

  passed = False
  response_headers = None
  failures = None

  def __init__(self):
    self.failures = list()

  def __str__(self):
    return json.dumps(self, default=safe_to_json)


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
      test_config.variable_binds.update(parsing.flatten_dictionaries(value)['data'])
    elif key == 'generator':
      flat = parsing.flatten_dictionaries(value)['data']
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

def session_handle(request,test_config=TestConfig(),session_handle=None, *args, **kwargs):
  verify = True
  stream = False
  cert = None

  if not session_handle:
    session_handle = requests.Session()
  prepped = request.prepare()
  if test_config.ssl_insecure:
    session_handle.verify = False
  if test_config.stream :
    session_handle.stream = True
  if test_config.cert :
    session_handle.cert = test_config.cert
  
  response = session_handle.send(prepped)
  return response

def run_test(mytest,test_config=TestConfig(), context=None, request_handler=None, *args, **kwargs):
  
  my_context = context
  if my_context is None:
    my_context = Context()

  mytest.update_context_before(my_context)
  templated_test = mytest.realize(my_context)
  request = templated_test.configure_request(
    timeout=test_config.timeout, context=my_context,request_handler=request_handler)
  


  result = TestResponse()
  result.test = templated_test
  session_handler = requests.Session()

  print("--------------------------------------------")
  print("Test Name\t:\t{}\n".format(mytest.name))

  print("--------------------------------------------")
  try:
    respons = session_handle(request,test_config=test_config,session_handle=session_handler)
  except Exception as e:
    trace = traceback.format_exc()
    result.failures.append(Failure(message="Exception Happens: {}".format(str(e)),
    details=trace, failure_type=validators.FAILURE_REQUESTS_EXCEPTION))
    result.passed = False
  
  ## Retrieve Values
  result.body = util.convert(respons.content)
  result.response_headers = respons.headers
  result.response_code = respons.status_code
  respons_code = respons.status_code

  if respons_code in mytest.expected_status:
    result.passed = True
  else:
    result.passed = False
    failure_message = "Invalid HTTP response code, {} is not in expected status code".format(respons_code)
    result.failures.append(Failure(message=failure_message,details=None,failure_type=validators.FAILURE_INVALID_RESPONSE))
  
  head = result.response_headers
  if result.passed is True:
    body = result.body
    if mytest.validators is not None and isinstance(mytest.validators, list):
      failures = result.failures
      for validator in mytest.validators:
        validate_result = validator.validate(
          body=body, headers=head, context=my_context)
        if not validate_result:
          result.passed = False
        if hasattr(validate_result,'details'):
          failures.append(validate_result)
    
    mytest.update_context_after(result.body,head,my_context)
    if test_config.print_bodies or not result.passed:
      if test_config.interactive:
        print("RESPONSE:")
      print('--------------------------')
      print(result.body)
  
  logger.debug(result)
  
  return result


def read_file(path):
  """ Read an input into a file, doing necessary conversions around relative path handling """
  with open(path, "r") as f:
    string = f.read()
    f.close()
  return string

def log_failure(failure, context=None, test_config=TestConfig()):
  """ Log a failure from a test """
  logger.error("Test Failure, failure type: {}, Reason: {}".format(
    failure.failure_type, failure.message	))
  if failure.details:
    logger.error("Validator/Error details:" + str(failure.details))

def run_testsets(testsets):
  """ Execute a set of tests """
  group_results = dict()
  group_failure_counts = dict()
  total_failures = 0
  myinteractive = False
  requests_handler = requests.Request()

  for testset in testsets:
    mytest = testset.tests
    myconfig = testset.config
    context = Context()

    if myconfig.variable_binds:
      context.bind_variables(myconfig.variable_binds)
    if myconfig.generators:
      for key,value in myconfig.generators.items():
        context.add_generator(key,value)

    if not mytest:
      break

    myinteractive = True if myinteractive or myconfig.interactive else False

    for test in mytest:
      
      if test.group not in group_results:
        group_results[test.group] = list()
        group_failure_counts[test.group] = 0

      result = run_test(test,test_config=myconfig,context=context,request_handler=requests_handler)
      result.body = None

      if not result.passed:
        logger.error('Test Failed: ' + test.name + " URL=" + result.test.url +
          " Group=" + test.group + " HTTP Status Code: " + str(result.response_code))

        if result.failures:
          for failure in result.failures:
            log_failure(failure, context=context, test_config=myconfig)

        failures = group_failure_counts[test.group]
        failures = failures + 1
        group_failure_counts[test.group] = failures
      else:
        logger.info('Test Succeeded: ' + test.name +
                    'URL= '+ test.url + ' Group=' + test.group)
      
      group_results[test.group].append(result)

      if not result.passed and test.stop_on_failure is not None and test.stop_on_failure:
        print(
          "STOP ON FAILURE! Stopping test set execution, continuing with other test sets")
        break

  if myinteractive :
    print("===========================")

  for group in sorted(group_results.keys()):
    test_count = len(group_results[group])
    failures = group_failure_counts[group]
    total_failures = total_failures - failures

    passfail = {True: u'SUCCEEDED', False: u'FAILED: '}
    output_string = "Test Group {} {}: {}/{} Tests Passed!".format(group, passfail[failures == 0], str(test_count - failures), str(test_count))

    if myconfig.skip_term_colors:
      print(output_string)
    else:
      if failures > 0:
        print('033[91m' + output_string + '\033[0m')
      else:
        print('033[92m' + output_string + '\033[0m')
  
  return total_failures