import string
import os
import copy
import json
import sys
import hashlib
import string
from requests.auth import HTTPDigestAuth,HTTPBasicAuth
from requests_oauthlib import OAuth1,OAuth2,OAuth1Session,OAuth2Session
from requests.auth import AuthBase,_basic_auth_str

AUTH_TYPE = ['oauth1','basic','bearer','digest','oauth2']
AUTHENTICATORS = dict()

class BearerAuth(AuthBase):
    "Class to Generate Bearer Token on Authorizaation"

    def __init__(self,token):
        if 'bearer' in token.lower():
            self.Authorization = token
        else:
            self.Authorization = "Bearer " + token
    
    def __eq__(self,other):
        return all([self.Authorization == getattr(other,'Authorization',None)])
    
    def __ne__(self,other):
        return not self == other

    def __call__(self,r):
        r.headers['Authorization'] = self.Authorization






class Auth(object):
    
    name = None
    authentication = None
    authdata = None
    is_templated = False
    args = None
    query = None
    config = None

 
    def templated_query(self,context=None):
        query = self.query
        if context and self.is_templated:
            query = string.Template(query).safe_substitute(context.get_values())
        return query

    @classmethod
    def configure_base(cls,config,authenticator_base):
        if isinstance(config,dict) and 'template' in config:
            try:
                config = config['template']
                authenticator_base.is_templated = True
                authenticator_base.config = config
            except KeyError:
                raise ValueError("Cannot define a dictionary config for authorization without key")
        elif isinstance(config,dict):
            authenticator_base.config = config
            authenticator_base.is_templated = False
        
        elif isinstance(config,str):
            authenticator_base.is_templated = False
            authenticator_base.config = config
        else:
            raise TypeError(
                "Authenticators must have a string or {template : querystring} configuration node"
            )

        return authenticator_base


class BasicAuthenticators(Auth):
    "Basic Username Password Authentication"

    authentication_type = "basic"
    name = None
    config = dict()
    headers = dict()
    auth_location = None

    def get_auth(self,args=None):
        mydata = copy.copy(self.config)
        username = mydata['username']
        password = mydata['password']
        auth = HTTPBasicAuth(username,password)    
        return auth

    def get_headers(self,args=None):
        self.headers = copy.copy(self.config)
        return self.headers

    @classmethod
    def parse(cls,config):
        base = BasicAuthenticators()
        return cls.configure_base(config,base)
        return base



class OAuth1Authenticators(Auth):
    "Standard OAuth1 Authentication from requests"
    authentication_type = "oauth1"
    name = None
    config = dict()

    def get_auth(self,args=None):
        mydata = copy.copy(self.config)
        app_key = mydata['consumerkey']
        app_secret = mydata['consumersecret']
        token = mydata['token']
        secret = mydata['tokensecret']

        auth = OAuth1(app_key,app_secret,resource_owner_key=token,
                        resource_owner_secret=secret)
        
        return auth

    def get_headers(self):
        mydata = copy.copy(self.config)
        return mydata


    @classmethod
    def parse(cls,config):
        base = OAuth1Authenticators()
        return cls.configure_base(config,base)
        return base

class DigestAuthenticators(Auth):
    "Standard Digest Authentication from requests"
    authentication_type = "digest"
    name = None
    config = dict()

    headers = dict()

    def get_auth(self,args=None):
        mydata = copy.copy(self.config)
        username = mydata['username']
        password = mydata['password']
        auth = HTTPDigestAuth(username,password)
        return auth

    def get_headers(self,args=None):
        self.headers = copy.copy(self.config)
        return self.headers

    @classmethod
    def parse(cls,config):
        base = DigestAuthenticators()
        return cls.configure_base(config,base)
        return base


class BearerAuthentication(Auth):
    "Basic Username Password Authentication"

    authentication_type = "bearer"
    name = None
    config = dict()
    headers = dict()
    auth_location = None

    def get_auth(self,args=None):
        mydata = copy.copy(self.config)
        token = mydata['Authorization']
      
        auth = BearerAuth(token)
        return auth


    def get_headers(self,args=None):
        self.headers['Authorization'] = self.config['Authorization']
        return self.headers

    @classmethod
    def parse(cls,config):
        if config['token'].split(" ")[0] != "Bearer":
            token = "Bearer "+config["token"]
        else:
            token = config['token']
        config = dict()
        config['Authorization'] = token
        base = BearerAuthentication()
        return cls.configure_base(config,base)
        return base





def register_authenticators(authenticator_type,authenticator_function):
    if not isinstance(authenticator_type,str):
        raise TypeError("Authenticator type must be string")
    elif authenticator_type in AUTHENTICATORS:
        raise ValueError("Authenticator {} is already exists".format(authenticator_type))
    AUTHENTICATORS[authenticator_type] = authenticator_function




def parse_authenticators(name,config_node):
    name = name.lower()
    if name not in AUTHENTICATORS:
        raise ValueError("Auth {} is not implemented yet".format(name))
   
    auth = AUTHENTICATORS[name](config_node)
    
    if auth.name is None:
        auth.name = name
    if auth.config is None:
        auth.config = config_node
    return auth




register_authenticators("basic",BasicAuthenticators.parse)
register_authenticators("oauth1",OAuth1Authenticators.parse)
register_authenticators("digest",DigestAuthenticators.parse)
register_authenticators("bearer",BearerAuthentication.parse)
register_authenticators("oauth2",BearerAuthentication.parse)