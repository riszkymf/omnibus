import json
import os
import jmespath
import yaml
from omnibus.libs import util


def postman_convert_variables(postman_text):
    """ Convert postman variables binding 
        e.g : {url: {{domain}}/endpoint } to omnibus' format
        url : $domain/endpoint
    """
    if "{{" in postman_text and "}}" in postman_text:
        tmp = postman_text.replace("{{","$")
        tmp = tmp.replace("}}","")
        return util.generate_respons(True,tmp)
    else:
        return util.generate_respons(False,postman_text)

def clean_raw_string(txt):

    temp = txt.expandtabs().replace(" ","").splitlines()
    result = ""
    for i in temp:
        result+=i
    return result

def parse_postman_auth(data):
    auth = dict()
    result = dict()
    for item in data[data['type']]:
        auth[item['key']] = item['value']
    result[data['type']] = auth
    return result


def parse_postman_variables(data):
    binded = dict()
    for item in data:
        if item['type'].lower() == 'string':
            binded[item['key']] = item['value']
        elif item['type'].lower() == 'integer':
            binded[item['key']] = int(item['value'])
    return binded


def parse_postman_config(myjson):
    
    json_path = [('testset','info.name'),('desc','info.description'),('authorization','auth'),('variable_binds','variable')]
    config = list()
    for key,path in json_path:
        config_details = dict()
        try:
            if key == 'authorization' or key == 'auth':
                config_details[key] = parse_postman_auth(myjson['auth'])
            elif key == 'variable_binds':
                config_details[key] = parse_postman_variables(myjson['variable'])
            else:
                config_details[key] = jmespath.search(path,myjson)
        except:
            pass
        config.append(config_details)
    return config

def parse_postman_body(p_string):
    if not p_string[p_string["mode"]]:
        return False
    else:
        if p_string["mode"] == "formdata":
            txt = ""
            for i in p_string["formdata"]:
                txt+= '"{}" : "{}",'.format(i['key'],i['value'])
            txt = "{" + txt.rstrip(",") + "}"
            clean_body = clean_raw_string(txt)
        else:
            clean_body = clean_raw_string(p_string[p_string["mode"]])
        return clean_body


def parse_postman_test(mytest):
    listed_test = list()

    # json_path = [('name','name'),('method','request.method'),('headers','request.header'),('url','request.url.raw'),('body','request.body'),('exec',"event[?listen == 'test'].script.exec[]")]
    json_path = [('name','name'),('method','request.method'),('headers','request.header'),('url','request.url.raw'),('body','request.body'),('exec',"event[?listen == 'test'].script.exec[]")]
    templated = {'url' : False, 'headers':False, 'body':False,' event':False}

    for key,path in json_path:
        test_detail = dict()
        try:
            if key == 'body':
                if parse_postman_body(jmespath.search(path,mytest)):
                    resp_body = parse_postman_body(jmespath.search(path,mytest))
                    resp_body = postman_convert_variables(resp_body)
                    templated[key] =resp_body['status']
                    if templated[key]:   
                        test_detail[key] = { "template" : {resp_body['data']}}
                    else:
                        test_detail[key] = resp_body["data"]
            elif key == 'headers':
                for val in jmespath.search(path,mytest):
                    tmp_dict = dict()
                    resp_head = postman_convert_variables(val['value'])
                    templated[key] = templated[key] or resp_head["status"]
                    tmp_dict[val['key']] = resp_head["data"]
                if templated[key]:
                    test_detail[key] = {"template" : tmp_dict}
                else:
                    test_detail[key] = tmp_dict
            elif key == 'exec':
                val = jmespath.search(path,mytest)
                test_script = parse_postman_script(val)
                try:
                    for x,y in test_script.items():
                        print("KEY : ",x)
                        print("VAL : ",y)
                        test_detail[x] = y
                except:
                    pass
            else:
                if key in list(templated.keys()):
                    tmp_data = postman_convert_variables(jmespath.search(path,mytest))       
                    if tmp_data["status"]:        
                        test_detail[key] = {"template" : tmp_data["data"]}
                    else:
                        test_detail[key] = tmp_data["data"]
                else:
                    test_detail[key] = jmespath.search(path,mytest)                        
        except:
            pass
        if test_detail:
            listed_test.append(test_detail)
    return listed_test



    

def parse_postman(test_file):
    try:
        postman_data = util.load_json(test_file)
    except Exception as e:
        print(str(e))
        return 0
    mytest = list()
    myconfig = { "config" : parse_postman_config(postman_data) }
    mytest.append(myconfig)
    for i in postman_data['item']:
        mytest.append({"test" : parse_postman_test(i)})
    
    return mytest
    
def parse_postman_script(text):
    script = list()
    start = False
    tmp_yaml = ""

    for i in text:
        if "`omnibus" in i:
            start = True
            continue
        if i == "`":
            break
        elif start:
            script.append(i)
            tmp_yaml += i + "\n"

    result = yaml.load(tmp_yaml)
    return result
