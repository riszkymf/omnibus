import os
import sys
import threading
import json
import requests
import logging
import pycurl
import traceback

from . import generator
from . import parsing
from . import util
from . import binding
from .six import text_type
from . import validators
from .tests import Test, DEFAULT_TIMEOUT
from .binding import Context
from .validators import Failure
from email import message_from_string

from io import BytesIO as MyIO

DIR_LOCK = threading.RLock()
HEADER_ENCODING ='ISO-8859-1' # Per RFC 2616

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
    print_bodies = False
    print_headers = False
    variable_binds = False
    generators = False
    scope = None
    url = None
    verbose = False
    ssl_insecure = False
    stream = False
    cert = None
    is_dumped = False
    interactive = False
    skip_term_colors = False
    is_flask = True
    flask_app = None
    is_remote = False
    is_request = False
    is_curl = False
    endpoint = None
    global_headers = None
    filename = None


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
        return json.dumps(self, default=safe_to_json)



def parse_file(test_structure, test_files=set(), working_directory=None, vars=None, global_url=None):
    """" Parse test content from single file """
    test_out = list()
    test_config = TestConfig()
    tests_out = list()
    testsets = list()
    url = None
    global_endpoint = None

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
                    if 'flask' in parsing.flatten_dictionaries(node[key])['data']:
                        flaskapp = parsing.flatten_dictionaries(node[key])['data']['flask']
                    if 'endpoint' in parsing.flatten_dictionaries(node[key])['data']:
                        global_endpoint= parsing.flatten_dictionaries(node[key])['data']['endpoint']
                    test_config = parse_configuration(
                    node[key], base_config=test_config)
                elif key == 'test':
                    with cd(working_directory):
                        child = node[key]
                        mytest = Test.parse_test(global_url, child, global_endpoint=global_endpoint)
                        f_name = test_files.split('/')[-1]
                        mytest.name = f_name
                        test_config.filename = f_name
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
        elif key == 'endpoint':
            test_config.endpoint = str(value)
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
            test_config.generators = gen_map
        elif key == 'flask':
            temp = parsing.flatten_dictionaries(value)['data']
            path = temp['path']
            app_name = temp['name']
            try:
                try:
                    test_config.flask_app = getattr(__import__(path),app_name)
                except:
                    sys.path.append(os.getcwd())
                    test_config.flask_app = getattr(__import__(path),app_name)
            except Exception as e:
                print('\033[91m ERROR ON IMPORTING FLASK APPLICATION, ERROR MESSAGE : {}\033[0m'.format(str(e)))
                print('\033[91m CHECK YOUR FLASK APP ON YOUR TEST CONFIGURATION \033[0m')
        elif key == 'headers':
            test_config.global_headers = value
    return test_config



def parse_headers(header_string):
    """ Parse a header-string into individual headers
        Implementation based on: http://stackoverflow.com/a/5955949/95122
        Note that headers are a list of (key, value) since duplicate headers are allowed

    """
    # First line is request line, strip it out
    if not header_string:
        return list()
    request, headers = header_string.split('\r\n', 1)
    if not headers:
        return list()
    header_msg = message_from_string(headers)
    # Note: HTTP headers are *case-insensitive* per RFC 2616
    return [(k.lower(), v) for k, v in header_msg.items()]




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
  
    if test_config.interactive or (test_config.print_bodies or test_config.print_headers):
        print("--------------------------------------------")
        print("Test Name\t:\t{}\n".format(mytest.name))
        print("--------------------------------------------")
        
        ## Test using requests, currently cant use coverage
    if test_config.is_remote:
        if test_config.is_request:
            request = templated_test.configure_request(
                timeout=test_config.timeout, context=my_context,request_handler=request_handler)
            result = TestResponse()
            result.test = templated_test
            session_handler = requests.Session()
            if test_config.interactive:
                print("==========================================")
                print("%s" % mytest.name)
                print("------------------------------------------")
                print("REQUEST:")
                print("%s %s" %(templated_test.method, templated_test.url))
                print("HEADERS:")
                print("%s"%(templated_test.headers))
                if mytest.body is not None:
                    print("\n BODY:\n %s" %templated_test.body)
                input("Press ENTER to continue (%d): " %(mytest.delay))
            try:
                respons = session_handle(request,test_config=test_config,session_handle=session_handler)
            except Exception as e:
                trace = traceback.format_exc()
                result.failures.append(Failure(message="Exception Happens: {}".format(str(e)),
                details=trace, failure_type=validators.FAILURE_REQUESTS_EXCEPTION))
                result.passed = False
            ## Retrieve Values
            result.body = util.convert(respons.content)
            respons.headers = respons.headers.items()
            result.response_headers = respons.headers
            result.response_code = respons.status_code
            response_code = respons.status_code
    elif test_config.is_curl:
        curl_handle = pycurl.Curl()
        curl = templated_test.configure_curl(
            timeout=test_config.timeout, context=my_context,curl_handle=curl_handle)
        result = TestResponse()
        headers = MyIO()
        body = MyIO()
        curl.setopt(pycurl.WRITEFUNCTION, body.write)
        curl.setopt(pycurl.HEADERFUNCTION, headers.write)
        if test_config.verbose:
            curl.setopt(pycurl.VERBOSE, True)
        if test_config.ssl_insecure:
            curl.setopt(pycurl.SSL_VERIFYPEER,0)
            curl.setopt(pycurl.SSL_VERIFYHOST,0)
        result.passed = None

        if test_config.interactive:
            print("==========================================")
            print("%s" % mytest.name)
            print("------------------------------------------")
            print("REQUEST:")
            print("%s %s" %(templated_test.method, templated_test.url))
            print("HEADERS:")
            print("%s"%(templated_test.headers))
            if mytest.body is not None:
                print("\n BODY:\n %s" %templated_test.body)
            input("Press ENTER to continue (%d): " %(mytest.delay))

        try:
            curl.perform()
        except Exception as e:
            trace = traceback.format_exc()
            result.failures.append(Failure(message="Curl Exception: {}".format(str(e))))
            result.passed = False
            curl.close()
            return result

        result.body = body.getvalue()
        body.close()
        result.response_headers = text_type(headers.getvalue(), HEADER_ENCODING)
        headers.close()

        response_code = curl.getinfo(pycurl.RESPONSE_CODE)
        result.response_code = response_code

        if response_code in mytest.expected_status:
            result.passed = True
        else:
            result.passed = False
            failure_message = "Invalid HTTP Response Code: Code {} is not expected".format(response_code)
            result.failures.append(Failure  (message=failure_message,details=None,failure_type=validators.FAILURE_INVALID_RESPONSE))
        try:
            result.response_headers = parse_headers(result.response_headers)
        except Exception as e:
            trace = traceback.format_exc()
            result.failures.append(Failure(message="Header parsing exception: {0}".format(
                e), details=trace, failure_type=validators.FAILURE_TEST_EXCEPTION))
            result.passed = False
            curl.close()
            return result

        # print str(test_config.print_bodies) + ',' + str(not result.passed) + ' ,
        # ' + str(test_config.print_bodies or not result.passed)

        head = result.response_headers

        # execute validator on body
        if result.passed is True:
            body = result.body
            if mytest.validators is not None and isinstance(mytest.validators, list):
                logger.debug("executing this many validators: " +
                            str(len(mytest.validators)))
                failures = result.failures
                for validator in mytest.validators:
                    validate_result = validator.validate(
                        body=body, headers=head, context=my_context)
                    if not validate_result:
                        result.passed = False
                    # Proxy for checking if it is a Failure object, because of
                    # import issues with isinstance there
                    if hasattr(validate_result, 'details'):
                        failures.append(validate_result)
                    # TODO add printing of validation for interactive mode
            else:
                logger.debug("no validators found")

            # Only do context updates if test was successful
            mytest.update_context_after(result.body, head, my_context)

        

    elif test_config.is_flask:
        app = test_config.flask_app()
        if test_config.interactive:
            print("==========================================")
            print("%s" % mytest.name)
            print("------------------------------------------")
            print("REQUEST:")
            print("%s %s" %(templated_test.method, templated_test.url))
            print("HEADERS:")
            print("%s"%(templated_test.headers))
            if mytest.body is not None:
                print("\n BODY:\n %s" %templated_test.body)
            input("Press ENTER to continue (%d): " %(mytest.delay))
        respons = templated_test.configure_flask_test(context=my_context,app=app)
        headers = dict()
        result = TestResponse()
        result.test = templated_test
        for key,val in list(respons.headers):
            headers[key] = val
        result.response_headers = headers.items()
        result.response_code = respons.status_code
        response_code = respons.status_code
        ##convert body
        #result.body = json.loads(respons.data.decode('utf8'))               
        result.body = util.convert(respons.data)


    if response_code in mytest.expected_status:
        result.passed = True        
    else:
        result.passed = False
        failure_message = "Invalid HTTP response code, {} is not in expected status code".format(response_code)
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

    if test_config.print_headers or not result.passed:
        if test_config.interactive:
            print("HEADERS:")
        print('--------------------------')
        print(result.response_headers)
  
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
            
            if not test.headers:
                test.headers = myconfig.global_headers
            

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
        output_string = "Test Group {}, on {}, {}: {}/{} Tests Passed!".format(group,myconfig.filename, passfail[failures == 0], str(test_count - failures), str(test_count))

        if myconfig.skip_term_colors:
            print(output_string)
        else:
            if failures > 0:
                print('\033[91m' + output_string + '\033[0m')
            else:
                print('\033[92m' + output_string + '\033[0m')
  
    return total_failures