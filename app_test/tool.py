import yaml
import json
from omnibus.libs.util import *
from os import getcwd


def get_test_data():
    path = 'data_static/data.yaml'
    cwd = getcwd()
    path = get_path(cwd,path)
    data=load_yaml(path)
    data = [i['identity'] for i in data]
    return data

def generate_respons_test(status_code,data,status):
    d = {'response_code':status_code,
         'data'         :data,
         'status'       :status}
    return json.dumps(d)

def generate_fake_data():
    data = [{'identity': {'firstname': 'John',
            'lastname': 'Doe',
            'id': 1,
            'email': 'JohnDoe@gmail.com'}},
            {'identity': {'firstname': 'Gregory',
            'lastname': 'House',
            'id': 2,
            'email': 'House@gmail.com'}},
            {'identity': {'firstname': 'Joe',
            'lastname': 'Quimby',
            'id': 3,
            'email': 'JoeQuimby@gmail.com'}},
            {'identity': {'firstname': 'Herschel',
            'lastname': 'Krustofsky',
            'id': 4,
            'email': 'Krusty@gmail.com'}},
            {'identity': {'firstname': 'Waylon',
            'lastname': 'Smithers',
            'id': 5,
            'email': 'Smithers@gmail.com'}},
            {'identity': {'firstname': 'Eric',
            'lastname': 'Cartman',
            'id': 6,
            'email': 'Cartman@gmail.com'}}]
    
    path = 'data_static/data.yaml'
    path = get_path(getcwd(),path)
    yaml_data = yaml.dump(data)
    generate_file(path,yaml_data)

def write_new_data(data):
    data_ = list()
    for i in data:
        data_.append({'identity': i})
    print(data)
    path = 'data_static/data.yaml'
    path = get_path(getcwd(),path)
    yaml_data = yaml.dump(data_)
    generate_file(path,yaml_data)