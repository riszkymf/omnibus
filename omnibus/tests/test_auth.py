import pytest
import sys


sys.path.append('/home/mfriszky/worksworksworks/branch-sandbox/RESTKnot/API/omnibus/omnibus')
from omnibus.libs.auth import *


class TestAuth():
    
    def test_bearer_auth(self):
        auth_data = {'bearer': {'token' : 'testtoken'}}
        auth_base = parse_authenticators('bearer',auth_data['bearer'])
        header = auth_base.get_headers()
        auth = auth_base.get_auth()
        result = {'Authorization' : 'Bearer testtoken'}
        assert header == result
        assert auth.Authorization == result['Authorization']

    def test_basic_auth(self):
        auth_data = {'username' : 'user', 'password': 'pwd'}
        auth_base = parse_authenticators('basic',auth_data)
        header = auth_base.get_headers()
        assert header == auth_data
        auth = auth_base.get_auth()
        assert auth.username == 'user'
        assert auth.password == 'pwd'

    def test_digest_auth(self):
        auth_data = {'username' : 'user', 'password': 'pwd'}
        auth_base = parse_authenticators('digest',auth_data)
        header = auth_base.get_headers()
        assert header == auth_data
        auth = auth_base.get_auth()
        assert auth.username == 'user'
        assert auth.password == 'pwd'

    def test_oauth1_auth(self):
        auth_data = {'consumerkey' : 'mykey', 'consumersecret':'mysecret','token': 'apptoken', 'tokensecret': 'appsecret'}
        auth_base = parse_authenticators('oauth1',auth_data)
        auth = auth_base.get_auth()
        head = auth_base.get_headers()
        assert auth
        assert head == auth_data