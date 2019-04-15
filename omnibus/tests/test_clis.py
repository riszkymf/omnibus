import pytest
import sys
import os
import subprocess


class TestCLIS():

    def test_test_cov(self):
        argsall = 'omnibus cov ../tests/flask_test/ --source ../app/controllers/api/ --dir appcov --report html --rcfile ../.coveragec'
        args = argsall.split(' ')
        result = subprocess.check_call(args)

    def test_run_flask(self):
        argsall = 'omnibus run ../tests/flask_test/ -f'
        args = argsall.split(' ')
        result = subprocess.check_call(args)


    def test_run_request(self):
        argsall = 'omnibus run ../tests/ignore/requests/test_zone.yml -r --report html'
        args = argsall.split(' ')
        result = subprocess.check_call(args)

    def test_run_curl(self):
        argsall = 'omnibus run ../tests/ignore/curl/test_zone.yml -c'
        args = argsall.split(' ')
        result = subprocess.check_call(args)

    def test_run_postman(self):
        argsall = 'omnibus run ../tests/postman/test_postman_short.json --pm -r --report html'
        args = argsall.split(' ')
        result = subprocess.check_call(args)

    def test_run_benchmark(self):
        argsall = 'omnibus run ../tests/test_benchmark.yml -r'
        args = argsall.split(' ')
        result = subprocess.check_call(args)

    def test_xml_report(self):
        argsall = 'omnibus run ../tests/test_ttl.yml -r --report xml'
        args = argsall.split(' ')
        result = subprocess.check_call(args)

    