import json
import pprint
import os
from lxml import etree
from libs.util import *
from libs.parsing import safe_to_json


class Reports(object):

    summary = dict()
    test_name = "Default"
    request_details = dict()


    def __init__(self):
        self.summary = {
            "method": False,
            "expected_status": list(),
            "group": "",
            "status": False,
            "url": "",
            "test_name": ""
        }
        self.request_details = {
            "headers": dict(),
            "body": dict(),
            "params": dict(),
            "validators": list()
        }
        self.result_details = {
           "response_headers": dict(),
           "status_code": None,
           "passed": False,
           "failures": list(),
           "response_body": dict() 
        }

    def prepare_for_jinja(self):
        pass

class BenchmarkReports(object):

    summary = dict()
    test_name = "Default"
    request_details = dict()


    def __init__(self):
        self.summary = {
            "method": False,
            "expected_status": list(),
            "group": "",
            "fails": False,
            "url": "",
            "test_name": "",
            "benchmark_runs": 1,
            "concurrency": 1
        }

        self.benchmark_results = dict()


    def normalize_aggregates(self,values):
        res = dict()
        for metrics,aggr,value in values:
            if metrics not in list(res.keys()):
                res[metrics] = dict()
                res[metrics][aggr] = value
            else:
                res[metrics][aggr] = value
        return res

    def normalize_bench_result(self,values):
        res = dict()
        for key,val in values.items():
            res[key] = val
        return res

    def prepare_plot(self,report):
        cfgs = list()
        for key,data in report.benchmark_results['results'].items():
            labels = [i for i in range(1,len(data)+1)]
            data_plots = [{"x": x, "y": y} for x,y in zip(labels,data)]
            cfg = { "name": key,
                    "config":
                    {"type": "line",
                            "data": {
                                "labels": labels,
                                "datasets":[{
                                "borderWidth":1,
                                "pointRadius":5,
                                "pointHoverRadius":7,
                                "pointBackgroundColor":"rgb(71, 134, 237)",
                                "data": data_plots ,
                                "label": key
                                }]
                            }
                        }
                    }
            cfgs.append(cfg)
        self.data_chart = cfgs
        return cfgs
