import pytest
import sys
import os
import subprocess


class TestCLIS():

    def test_test_cov(self):
        argsall = 'omnibus cov ../tests/ --source ../app/controllers/api/ --dir appcov --report html --ignore ../tests/ignore/ --rcfile ../.coveragec'
        args = argsall.split(' ')
        result = subprocess.check_call(args)

    def test_run_request(self):
        argsall = 'omnibus run ../tests/requests/test_zone.yml -r'
        args = argsall.split(' ')
        result = subprocess.check_call(args)

    def test_run_curl(self):
        argsall = 'omnibus run ../tests/requests/test_zone.yml -c'
        args = argsall.split(' ')
        result = subprocess.check_call(args)

    def test_run_flask(self):
        argsall = 'omnibus run ../tests/requests/test_zone.yml -f'
        args = argsall.split(' ')
        result = subprocess.check_call(args)