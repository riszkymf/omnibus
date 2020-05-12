import requests,json
from .parsing import safe_to_bool,safe_to_json

DEFAULT_TIMEOUT = 10

class RequestHandlerConfig(object):

    use_cookies = False
    url = None
    auth = None
    data = dict()
    headers = dict()
    is_json = False
    params = None
    timeout = None
    request_object = "request"
    encoding = None
    cert = False
    key = False
    session_attribute = dict()

    def __init__(self,**kwargs):

        for key,val in kwargs.items():
            if key == 'use_cookies':
                self.request_object = "session"
            elif key == 'url' and val != None:
                self.url = val
            elif key == 'is_json':
                self.is_json = True
            elif key == 'timeout':
                self.timeout = DEFAULT_TIMEOUT
            elif key == 'proxies':
                self.session_attribute['proxies'] = val
            elif key == 'verify':
                self.session_attribute['verify'] = safe_to_bool(val)
            elif key == 'stream':
                self.session_attribute['stream'] = safe_to_bool(val)
            elif key == 'cert':
                self.session_attribute['cert'] = val
            elif key == 'key':
                self.key = val
            elif key == 'auth':
                self.auth = val.get_auth()
            elif key in dir(self) and not(key.startswith("__")):
                setattr(self,key,val)

        if self.is_json:
            self.headers.update({"content-type": "application/json"})
            self.data = safe_to_json(self.data)

        if self.key:
            self.session_attribute['cert'] = (self.cert,self.key)
        

class RequestsHandler(object):


    def __init__(self,req_cfg=RequestHandlerConfig()):
        self.mysession = requests.Session()
        self.session_prop = req_cfg.session_attribute
        self.prepreqs = None
        return self.mysession


    def get_request_property(self,req_cfg):
        req_prop = [i for i in dir(requests.Request()) if not(i.startswith("__"))]
        props = dict()
        for key in req_prop:
            val = getattr(req_cfg,key,False)
            if not val or val == None:
                props[key] = val
        return props

    def set_prepped_requests(self,method,req_cfg=RequestHandlerConfig()):
        method = method.upper()
        arguments = self.get_request_property(req_cfg)
        prepared_request = requests.Request(method=method,**arguments)
        self.prepared_request = prepared_request

    def send_request(self):
        res = self.mysession.send(self.prepared_request)
        return res
        
    def update_session(self,session=requests.Session()):
        self.mysession = session
        return session


        
