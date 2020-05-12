import os
import sys
import threading
import json
import requests
import logging
import pycurl
import traceback
import os
import copy
import csv

from .benchmarks import Benchmark, AGGREGATES, METRICS, parse_benchmark, parse_config
from . import reports as rep
from . import generator
from . import parsing
from . import util
from . import binding
from . import auth
from .reportsHandler import Reports as MyReport
from .reportsHandler import BenchmarkReports as BenchReport
from .jinjaHandler import JinjaHandler
from .six import text_type
from . import validators
from .tests import Test, DEFAULT_TIMEOUT
from .binding import Context
from .validators import Failure
from email import message_from_string
from lxml import etree as ET
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
    is_flask = False
    flask_app = None
    is_remote = False
    is_request = False
    is_curl = False
    endpoint = None
    global_headers = dict()
    filename = None
    is_reported = False
    report_type = ""
    reportdest = 'runcov'
    auth = None
    is_benchmarked = False


    def __str__(self):
        return json.dumps(self, default=safe_to_json)

class TestSet:
    """ Container for test sets """
    tests = list()
    config = TestConfig()
    report = list()

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
    benchmarks = list()
    global_endpoint = None

    if working_directory is None:
        working_directory = os.path.abspath(os.getcwd())

    if vars and isinstance(vars,dict):
        test_config.variable_binds = vars
    for node in test_structure:
        if isinstance(node,dict):
            node = parsing.lowercase_keys(node)
            for key in node:
                if key == 'config' or key == 'configuration':
                    if 'url' in parsing.flatten_dictionaries(node[key]):
                        global_url = parsing.flatten_dictionaries(node[key])['url']
                    if 'flask' in parsing.flatten_dictionaries(node[key]):
                        flaskapp = parsing.flatten_dictionaries(node[key])['flask']
                    if 'endpoint' in parsing.flatten_dictionaries(node[key]):
                        global_endpoint= parsing.flatten_dictionaries(node[key])['endpoint']
                    test_config = parse_configuration(
                    node[key], base_config=test_config)
                elif key == 'test':
                    with cd(working_directory):
                        child = node[key]
                        mytest = Test.parse_test(global_url, child, global_endpoint=global_endpoint)
                        f_name = test_files.split('/')[-1]
                        test_config.filename = f_name
                        tests_out.append(mytest)
                elif key == 'benchmark':
                    benchmark = parse_benchmark(global_url,node[key])
                    benchmarks.append(benchmark)
                    test_config.is_benchmarked = True
                    f_name = test_files.split('/')[-1]
                    test_config.filename = f_name

    testset = TestSet()
    testset.tests = tests_out
    testset.config = test_config
    testset.benchmarks = benchmarks
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
    failure_report = list()

    report = list()

    def __init__(self):
        self.failures = list()

    def __str__(self):
        return json.dumps(self, default=safe_to_json)


def parse_configuration(node, base_config=None):
    """ Parse yaml configuration as information """
    test_config = base_config
    if not test_config:
        test_config = TestConfig()
    node = parsing.lowercase_keys(parsing.flatten_dictionaries(node))
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
            test_config.variable_binds.update(parsing.flatten_dictionaries(value))
        elif key == 'generator':
            flat = parsing.flatten_dictionaries(value)
            gen_map = dict()
            for generator_name, generator_config in flat.items():
                gen = generator.parse_generator(generator_config)
                gen_map[str(generator_name)]= gen
            test_config.generators = gen_map
        elif key == 'flask':
            temp = parsing.flatten_dictionaries(value)
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
        
        elif key == 'auth' or key == 'authorization':
            tempauth = parsing.lowercase_keys(value)
            for key,val in tempauth.items():
                test_config.auth = auth.parse_authenticators(key,val)
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

    test_report = MyReport()

    report_summary = dict()
    report_request_details = dict()
    report_results = dict()
    my_context = context
    if my_context is None:
        my_context = Context()
    
    if test_config.auth:
        mytest.auth = test_config.auth

    mytest.update_context_before(my_context)
    templated_test = mytest.realize(my_context)
    
    report_summary = {
        "testsets" : getattr(test_config,"filename"),
        "test_name": getattr(templated_test,"name"),
        "method": getattr(templated_test,"method"),
        "group": getattr(templated_test,"group"),
        "expected_status": getattr(templated_test,"expected_status")
    }

    report_request_details =  {
        "validators" : [i.config for i in templated_test.validators],
        "headers": util.grab_and_convert(templated_test.headers,dict()),
        "params": util.grab_and_convert(templated_test.params,dict()),
        "body": util.grab_and_convert(templated_test.body,dict())
        }


    request = templated_test.configure_request(
        timeout=test_config.timeout, context=my_context,request_handler=request_handler)
    result = TestResponse()
    result.test = templated_test
    session_handler = requests.Session()
    try:
        respons = session_handle(request,test_config=test_config,session_handle=session_handler)
    except Exception as e:
        trace = traceback.format_exc()
        result.failures.append(Failure(message="Exception Happens: {}".format(str(e)),
        details=trace, failure_type=validators.FAILURE_REQUESTS_EXCEPTION))
        report_results = Failure(message="Exception Happens: {}".format(str(e)),details=trace, failure_type=validators.FAILURE_REQUESTS_EXCEPTION)
        return result
    
    ## Retrieve Values

    result.body = util.convert(respons.content)
    respons.headers = list(respons.headers.items())
    result.response_headers = respons.headers
    result.response_code = respons.status_code
    response_code = respons.status_code
    if response_code in mytest.expected_status:
        result.passed = True
    else:
        result.passed = False

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
    logger.debug(result)

    report_summary['status'] = result.passed
    report_summary['url'] = templated_test.url
    report_results = {
        "response_headers": respons.headers,
        "status_code": respons.status_code,
        "passed": result.passed,
        "response_body": result.body
    }
    test_report.summary.update(report_summary)
    test_report.request_details.update(report_request_details)
    test_report.result_details.update(report_results)
    return result,test_report


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
    result = TestResponse()
    jinjareports = list()
    total_test = 0
    fail_count = 0
    is_benchmark = False

    for testset in testsets:
        mytest = testset.tests
        myconfig = testset.config
        mybenchmarks = testset.benchmarks
        context = Context()
        if myconfig.variable_binds:
            context.bind_variables(myconfig.variable_binds)
        if myconfig.generators:
            for key,value in myconfig.generators.items():
                context.add_generator(key,value)

        if not mytest and not mybenchmarks:
            break

        myinteractive = True if myinteractive or myconfig.interactive else False

        for test in mytest:
            total_test = total_test + 1
            if test.group not in group_results:
                group_results[test.group] = list()
                group_failure_counts[test.group] = 0
            
            if not test.headers:
                test.headers = myconfig.global_headers

            if not test.url :
                test.url = test.local_url

            result,report_results = run_test(test,test_config=myconfig,context=context,request_handler=requests_handler)
            jinjareports.append(report_results)
            result.body = None
            if not result.passed:
                logger.error('Test Failed: ' + test.name + " URL=" + result.test.url +
                " Group=" + test.group + " HTTP Status Code: " + str(result.response_code))

                for i in result.report:
                    if not i.passed[0]:
                        result.failure_report.append(i)

                if result.failures:
                    for failure in result.failures:
                        log_failure(failure, context=context, test_config=myconfig)

                failures = group_failure_counts[test.group]
                failures = failures + 1
                fail_count = fail_count + 1
                group_failure_counts[test.group] = failures
            else:
                logger.info('Test Succeeded: ' + test.name +
                            'URL= '+ test.url + ' Group=' + test.group)
      
            group_results[test.group].append(result)

            if not result.passed and test.stop_on_failure is not None and test.stop_on_failure:
                print(
                "STOP ON FAILURE! Stopping test set execution, continuing with other test sets")
                break

    for group in sorted(group_results.keys()):
        test_count = len(group_results[group])
        failures = group_failure_counts[group]
        total_failures = total_failures - failures

        passfail = {True: u'SUCCEEDED', False: u'FAILED: '}
        output_string = "Test Group {}, on {}, {}: {}/{} Tests Passed!".format(group,myconfig.filename, passfail[failures == 0], str(test_count - failures), str(test_count))

        if failures > 0:
            print('\033[91m' + output_string + '\033[0m')
        else:
            print('\033[92m' + output_string + '\033[0m')


    try:
        success_rate = ((total_test-fail_count)/total_test)*100
    except ZeroDivisionError:
        success_rate = "Zero Divison Error"
    jinjatest = JinjaHandler(myconfig.filename,success_rate,jinjareports)
    html_render = jinjatest.build_jinja()
    return total_failures,jinjareports,html_render


def run_benchmarksets(testsets):
    """ Execute a set of tests """
    group_results = dict()
    group_failure_counts = dict()
    total_failures = 0
    myinteractive = False
    requests_handler = requests.Request()
    result = TestResponse()
    jinjareports = list()
    total_test = 0
    fail_count = 0

    for testset in testsets:
        mytest = testset.tests
        myconfig = testset.config
        mybenchmarks = testset.benchmarks
        context = Context()
        if myconfig.variable_binds:
            context.bind_variables(myconfig.variable_binds)
        if myconfig.generators:
            for key,value in myconfig.generators.items():
                context.add_generator(key,value)

        if not mytest and not mybenchmarks:
            break

        myinteractive = True if myinteractive or myconfig.interactive else False

        for benchmark in mybenchmarks:
            is_benchmark = True
            bench_rep = BenchReport()
            benchmark_report = {
                "url": benchmark.url,
                "name": benchmark.name,
                "method": benchmark.method,
                "benchmark_runs": benchmark.benchmark_runs,
                "concurrency": getattr(benchmark,"concurrency",False),
                "metrics": list(getattr(benchmark,"metrics",set()))
            }
            if not benchmark.metrics:
                logger.debug('Skipping Benchmark, no metrics to measure')
                continue
            
            logger.info("Benchmark Starting: "+ benchmark.name + 
            "Group: " + benchmark.group)
            benchmark_result = run_benchmark(
                benchmark, myconfig, context=context)
            report_result = {
                "aggregates": bench_rep.normalize_aggregates(benchmark_result.aggregates),
                "results": bench_rep.normalize_bench_result(benchmark_result.results),
                "failure": benchmark_result.failures
            }
            bench_rep.summary.update(benchmark_report)
            bench_rep.benchmark_results.update(report_result)
            jinjareports.append(bench_rep)
            logger.info("Benchmark Done "+ benchmark.name + "Group: "+ benchmark.group)
            


    for group in sorted(group_results.keys()):
        test_count = len(group_results[group])
        failures = group_failure_counts[group]
        total_failures = total_failures - failures

        passfail = {True: u'SUCCEEDED', False: u'FAILED: '}
        output_string = "Test Group {}, on {}, {}: {}/{} Tests Passed!".format(group,myconfig.filename, passfail[failures == 0], str(test_count - failures), str(test_count))

        if failures > 0:
            print('\033[91m' + output_string + '\033[0m')
        else:
            print('\033[92m' + output_string + '\033[0m')


    for rep in jinjareports:
        rep.prepare_plot(rep)
    jinjatest = JinjaHandler(myconfig.filename,"None",jinjareports,"benchmark")
    html_render = jinjatest.build_jinja()
    return total_failures,jinjareports,html_render


def report_blackbox_xml(myreport,filename):
    f_name = filename.split('/')[-1]
    f_name = filename.split('.')
    filename = f_name[0]+'.xml'
    xml_testsets = ET.Element("root")
    group = dict()
    for report in myreport:
        for key,val in report.reports:
            if key.lower() == 'group':
                if val[0] not in group:
                    group[val[0]] = [report]
                else:
                    group[val[0]].append(report)

    out = ''
    for key,val in group.items():
        xml_group = ET.Element("Group")
        xml_group.text = str(key)
        
        for report in val:
            xml_request = ET.Element("Request")
            for i in report.reports:
                if i[0].lower() == 'test_name':
                    xml_test = rep.get_xml(i)[0]
                temp=rep.get_xml(i)
                for i in temp:
                    xml_request.append(i)
            xml_response = ET.Element("Response")
            for i in report.results:
                temp = rep.get_xml(i)
                for i in temp:
                    xml_response.append(i)
            xml_test.append(xml_request)
            xml_test.append(xml_response)
            xml_group.append(xml_test)
        xml_testsets.append(xml_group)
    out = ET.tostring(xml_testsets,encoding="unicode",pretty_print=True)
    filename = os.path.join(os.getcwd(),filename)
    util.generate_file(filename,out)

def report_blackbox_html(myreports,f_name,failure=None):
    dest = os.path.dirname(f_name)
    dest = os.path.join(os.getcwd(),dest)
    rep.collect_source(dest)
    f_temp = f_name.split('.')
    f_name = f_temp[0]+'.html'
    
    rep.generate_html_test(myreports,f_name,failure)

def report_benchmark_html(benchmark_report,f_name):
    dest = os.path.dirname(f_name)
    dest = os.path.join(os.getcwd(),dest)
    rep.collect_source(dest)
    f_temp = f_name.split('.')
    f_name = f_temp[0]+'.html'
    rep.generate_benchmark_report(benchmark_report,f_name)

class BenchmarkResult:
    """ Stores benchmark results for reports"""
    group = None
    name = "noname"

    results = dict()
    aggregates = list()
    failures = 0

    def __init__(self):
        self.aggregates = list()
        self.results = list()

    def __str__(self):
        return json.dumps(self, default=safe_to_json)

def run_benchmark(benchmark, test_config=TestConfig(), context=None, *args, **kwargs):

    my_context = context
    if my_context is None:
        my_context = Context()
    warmup_runs = benchmark.warmup_runs
    benchmark_runs = benchmark.benchmark_runs
    message = ''
    if benchmark_runs <= 0:
        raise ValueError(
            "Invalid number of benchmark runs, must be > 0: "+ benchmark_runs)

    result = TestResponse()

    # NOTE : ADD MULTI URL ?
    output = BenchmarkResult()
    output.name = benchmark.name
    output.group = benchmark.group
    metricnames = list(benchmark.metrics)

    metricvalues = [METRICS[name] for name in metricnames]

    results = [list() for x in range(0,len(metricnames))]


    if benchmark.is_concurrent :
        concurrency = benchmark.concurrency
        cycle,remainder = util.calculate_cycle(benchmark_runs,concurrency)
        warmup_cycle,warmup_remainder = util.calculate_cycle(warmup_runs,concurrency)
        multicurl_handler = list()


        temp_multi = pycurl.CurlMulti()
        temp_multi.handles = []
        # for x in range(0,warmup_runs):
        #     curl = pycurl.Curl()
        #     if len(temp_multi.handles) == concurrency :
        #         multicurl_handler.append(temp_multi.handles)
        #         temp_multi = pycurl.CurlMulti()
        #         temp_multi.handles = []
        #     benchmark.update_context_before(my_context)
        #     templated = benchmark.realize(my_context)
        #     curl = templated.configure_curl(
        #         timeout=test_config.timeout, context=my_context, curl_handle=curl)
        #     curl.setopt(pycurl.WRITEFUNCTION, lambda x:None)
            
        #     temp_multi.handles.append(curl)
        #     if x == (warmup_runs-1) and len(multicurl_handler) < warmup_cycle:
        #         multicurl_handler.append(temp_multi.handles)
        #     else:
        #         curl.perform()

        # temp_list = list()
        # for object_list in multicurl_handler:
        #     temp_multi = pycurl.CurlMulti()
        #     temp_multi.handles = []
        #     for curl_object in object_list:
        #         temp_multi.handles.append(curl_object)
        #         temp_multi.add_handle(curl_object)
        #     temp_list.append(temp_multi)
        # multicurl_handler = temp_list
        
        # for item in multicurl_handler:
        #     num_handles = len(item.handles)
        #     while num_handles:
        #         while 1 :
        #             ret, num_handles = item.perform()
        #             if ret != pycurl.E_CALL_MULTI_PERFORM: 
        #                 break
        #         item.select(1.0)
        #     item.handles.clear()
        #     item.close()

        # logger.info('Warmup: '+ message+ ' finished')
        # logger.info('Benchmark: '+ message + ' starting')


        multicurl_handler = list()


        temp_multi = pycurl.CurlMulti()
        temp_multi.handles = []
        buffer = list()
        for x in range(0,benchmark_runs):
            buffer.append(MyIO())
            curl = pycurl.Curl()
            if len(temp_multi.handles) == concurrency :
                multicurl_handler.append(temp_multi.handles)
                temp_multi = pycurl.CurlMulti()
                temp_multi.handles = []
            benchmark.update_context_before(my_context)
            templated = benchmark.realize(my_context)               
            curl = templated.configure_curl(
                timeout=test_config.timeout, context=my_context, curl_handle=curl)
            curl.setopt(pycurl.WRITEFUNCTION, buffer[x].write)
            temp_multi.handles.append(curl)
            if x == (benchmark_runs-1) and len(multicurl_handler) < cycle:
                multicurl_handler.append(temp_multi.handles)
            else:
                try:
                    curl.perform()
                except Exception:
                    output.failures = output.failures + 1
                    curl.close()
                    curl = pycurl.Curl()
                    continue
        temp_list = list()
        for object_list in multicurl_handler:
            temp_multi = pycurl.CurlMulti()
            temp_multi.handles = []
            for curl_object in object_list:
                temp_multi.handles.append(curl_object)
                temp_multi.add_handle(curl_object)
            temp_list.append(temp_multi)
        multicurl_handler = temp_list
        index = 0
        for item in multicurl_handler:
            num_handles = len(item.handles)
            while num_handles:
                while 1 :
                    try:
                        ret, num_handles = item.perform()
                    except Exception as e:
                        output.failures += 1
                        for curl_handle in item.handles:
                            curl_handle.close()
                        item.close()
                    if ret != pycurl.E_CALL_MULTI_PERFORM: 
                        break
                item.select(1.0)
            count,good,bad = item.info_read()
            for j in good:
                for i in range(0,len(metricnames)):
                    results[i].append(j.getinfo(metricvalues[i]))
    else:
        curl = pycurl.Curl()
        logger.info("Warmup: " + message+ ' started')
        for x in range(0,warmup_runs):
            benchmark.update_context_before(my_context)
            templated = benchmark.realize(my_context)
            curl = templated.configure_curl(
                timeout=test_config.timeout, context=my_context, curl_handle=curl)
            curl.setopt(pycurl.WRITEFUNCTION, lambda x:None)
            curl.perform()
        logger.info('Warmup: '+ message+ ' finished')
        logger.info('Benchmark: '+ message + ' starting')
        for x in range(0,benchmark_runs):
            benchmark.update_context_before(my_context)
            templated = benchmark.realize(my_context)
            curl = templated.configure_curl(
                timeout=test_config.timeout, context=my_context, curl_handle=curl)
            curl.setopt(pycurl.WRITEFUNCTION, lambda x: None)
            try:                
                if x == (benchmark_runs-1):
                    raise ValueError
                else:
                    curl.perform()
            except Exception:
                output.failures = output.failures + 1
                curl.close()
                curl = pycurl.Curl()
                continue

            for i in range(0,len(metricnames)):
                results[i].append(curl.getinfo(metricvalues[i]))

        logger.info('Benchmark: '+ message+ ' ending')

    temp_results = dict()
    for i in range(0, len(metricnames)):
        temp_results[metricnames[i]] = results[i]
    output.results = temp_results
    return analyze_benchmark_results(output,benchmark)  

def analyze_benchmark_results(benchmark_result, benchmark):
    output = BenchmarkResult()
    output.name = benchmark_result.name
    output.group = benchmark_result.group
    output.failures = benchmark_result.failures

    # Copy raw metric arrays over where necessary
    raw_results = benchmark_result.results
    temp = dict()
    for metric in benchmark.raw_metrics:
        temp[metric] = raw_results[metric]
    output.results = temp

    # Compute aggregates for each metric, and add tuples to aggregate results
    aggregate_results = list()
    for metricname, aggregate_list in benchmark.aggregated_metrics.items():
        numbers = raw_results[metricname]
        for aggregate_name in aggregate_list:
            if numbers:  # Only compute aggregates if numbers exist
                aggregate_function = AGGREGATES[aggregate_name]
                aggregate_results.append(
                    (metricname, aggregate_name, aggregate_function(numbers)))
            else:
                aggregate_results.append((metricname, aggregate_name, None))

    output.aggregates = aggregate_results
    return output

def metrics_to_tuples(raw_metrics):
    """ Converts metric dictionary of name:values_array into list of tuples
        Use case: writing out benchmark to CSV, etc

        Input:
        {'metric':[value1,value2...], 'metric2':[value1,value2,...]...}

        Output: list, with tuple header row, then list of tuples of values
        [('metric','metric',...), (metric1_value1,metric2_value1, ...) ... ]
    """
    if not isinstance(raw_metrics, dict):
        raise TypeError("Input must be dictionary!")

    metrics = sorted(raw_metrics.keys())
    arrays = [raw_metrics[metric] for metric in metrics]

    num_rows = len(arrays[0])  # Assume all same size or this fails
    output = list()
    output.append(tuple(metrics))  # Add headers

    # Create list of tuples mimicking 2D array from input
    for row in range(0, num_rows):
        new_row = tuple([arrays[col][row] for col in range(0, len(arrays))])
        output.append(new_row)
    return output

def register_extensions(modules):
    """ Import the modules and register their respective extensions """
    if isinstance(modules, str):  
        modules = [modules]
    for ext in modules:
        segments = ext.split('.')
        module = segments.pop()
        package = '.'.join(segments)
        module = __import__(ext, globals(), locals(), package)

        extension_applies = {
            'VALIDATORS': validators.register_validator,
            'COMPARATORS': validators.register_comparator,
            'VALIDATOR_TESTS': validators.register_test,
            'EXTRACTORS': validators.register_extractor,
            'GENERATORS': generator.register_generator
        }

        has_registry = False
        for registry_name, register_function in extension_applies.items():
            if hasattr(module, registry_name):
                registry = getattr(module, registry_name)
                for key, val in registry.items():
                    register_function(key, val)
                if registry:
                    has_registry = True

        if not has_registry:
            raise ImportError(
                "Extension to register did not contain any registries: {0}".format(ext))

def write_benchmark_json(file_out, benchmark_result, benchmark, test_config=TestConfig()):
    """ Writes benchmark to file as json """
    print(file_out)
    json.dump(benchmark_result, file_out, default=safe_to_json)

def write_benchmark_csv(file_out, benchmark_result, benchmark, test_config=TestConfig()):
    """ Writes benchmark to file as csv """
    writer = csv.writer(file_out)
    writer.writerow(('Benchmark', benchmark_result.name))
    writer.writerow(('Benchmark Group', benchmark_result.group))
    writer.writerow(('Failures', benchmark_result.failures))

    # Write result arrays
    if benchmark_result.results:
        writer.writerow(('Results', ''))
        writer.writerows(metrics_to_tuples(benchmark_result.results))
    if benchmark_result.aggregates:
        writer.writerow(('Aggregates', ''))
        writer.writerows(benchmark_result.aggregates)


OUTPUT_METHODS = {'csv': write_benchmark_csv  ,'json': write_benchmark_json}

class TestSetHandler(object):
    TestSets = None

    def __init__(self,testsets,*args,**kwargs):
        pass

    def configure_test(self,**kwargs):
        for key,val in kwargs.items():
            pass