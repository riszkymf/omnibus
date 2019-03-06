import yaml
import os
import sys
import json

from os import listdir
from os.path import isfile, join


def generate_files(filename, data):

    generate_dir()
    d_names = generate_names(data)
    filename = check_filename(filename)
    test_file = open("{}.py".format(filename), "w+")

    test_file.write("import pytest")
    test_file.write("\n\n\n\n\n")
    test_file.write("################ CLASS ################")

    test_file.write("class {}")


def generate_names(d_dict):
    d_filename = list()
    d_classname = list()
    d_funcname = list()

    try:
        for f_name in d_dict:
            d_filename.append(f_name)
            for c_name in d_dict[f_name]:
                classname = f_name + "." + c_name
                d_classname.append(classname)
                for func_name in d_dict[f_name][c_name]["instances"]:
                    function_nm = f_name + "." + c_name + "." + func_name
                    d_funcname.append(function_nm)

        data = {
            "filenames": d_filename,
            "classnames": d_classname,
            "functionnames": d_funcname,
        }
        return generate_respons(True, data)
    except Exception as e:
        return generate_respons(False, message=str(e))


def load_yaml(filename):
    with open(filename, "r") as f:
        data = yaml.load(f)
        f.close()
    return data

def load_json(filename):
    with open(filename, "r") as f:
        data = json.load(f)
        f.close()
    return data    


def parse_yaml(f_name):
    d_yaml = load_yaml(f_name)

    filename = list()

    for row in d_yaml:
        filename.append(row)


def check_filename(filename):
    if "test_" not in filename:
        newname = "test_" + filename
        return newname
    else:
        if not filename.split("test_")[0]:
            newname = "test_" + filename.split("test_")[0]
            return newname
        else:
            return filename


def check_yaml(filename):
    return os.path.isfile(filename)


def generate_dir():
    if not os.path.isdir("tests"):
        os.mkdir("tests")


def generate_respons(status, data=None, message=None):
    respons = {"status": status, "data": data, "message": message}
    return respons


def copy_dict(dictionary):
    result = dict()
    for key, value in dictionary.items():
        result[key] = value
    return result


def convert(data):
    if isinstance(data, bytes):
        return data.decode()
    if isinstance(data, (str, int)):
        return str(data)
    if isinstance(data, dict):
        return dict(map(convert, data.items()))
    if isinstance(data, tuple):
        return tuple(map(convert, data))
    if isinstance(data, list):
        return list(map(convert, data))
    if isinstance(data, set):
        return set(map(convert, data))


def collect_file(folder):
    ext = ['yaml','yml']
    files_all = [ f for f in listdir(folder) if isfile(join(folder,f))]
    files = [folder+f for f in files_all if f.startswith('test_') and f.split('.')[1] in ext]
    
    return files


