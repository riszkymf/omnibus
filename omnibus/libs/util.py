import yaml
import os
import sys
import json

from os import listdir
from os.path import isfile,isdir, join, abspath


def generate_file(filename, data):

    generate_dir()

    try:
        with open("{}.txt".format(filename), "w+") as f:
            f.write(data)
            f.close()
            return True
    except:
        return False

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

def get_path(cwd,path):
    new_path = os.path.join(cwd,path)
    new_path = os.path.abspath(new_path)
    return new_path

def collect_file(folder,ignore=list()):
    ext = ['yaml','yml']
    files_all = [ f for f in listdir(folder) if isfile(join(folder,f))]
    files = [folder+f for f in files_all if f.startswith('test_') and f.split('.')[1] in ext and f not in ignore]
    
    return files

def check_exist(path):
    return os.path.exists(path)


def get_all(folder,ignores=list()):

    if not os.path.isabs(folder):
        folder = get_path(os.getcwd(),folder)
    if ignores:
        for i in ignores:
            if not os.path.isabs(i):
                i = get_path(os.getcwd(),i)

    files = list()
    dirs = [folder]
    ext = ['yaml','yml']
    def dive(f_data):
        if len(dirs) > 0:
            for d_dir in f_data:
                for d in listdir(d_dir):
                    path = join(d_dir,d)
                    if check_exist(path):
                        if isdir(path) and path not in ignores:
                            dirs.append(path)
                        if isfile(path) and d.startswith('test_') and path.split('.')[1] in ext and path not in ignores:
                            files.append(path)
                
                #[files.append(abspath(d)) for d in listdir(d_dir) if isfile(abspath(d)) and d.startswith('test_') and d.split('.')[1] in ext and d not in ignores]
                #[dirs.append(abspath(d)) for d in listdir(d_dir) if isdir(abspath(d))]
                dirs.remove(d_dir)
                break
                #print(files)
                #print(dirs)
            return dive(dirs)
    dive(dirs)
    return files


def get_path_files(filelist):
    """ Filelist format must be str """
    out_list = list()
    cwd = os.getcwd()
    if isinstance(filelist,str):
        filelist=filelist.split(',')
        for row in filelist:
            out_list.append(get_path(cwd,row))
        return out_list
    elif isinstance(filelist,list):
        for row in filelist:
            out_list.append(get_path(cwd,row))
        return out_list
    else:
        raise ValueError("Files format must be a list or str")