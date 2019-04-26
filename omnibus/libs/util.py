import yaml
import os
import sys
import math
import json

from urllib.parse import urlparse,urljoin
from os import listdir
from os.path import isfile,isdir, join, abspath

GLOBAL_HOME = os.path.expanduser("~")


def generate_file(filename, data):
    try:
        with open("{}".format(filename), "w+") as f:
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


def generate_dir(dirname):
    path = get_path(os.getcwd(),dirname)
    if not os.path.isdir(path):
        os.mkdir(path)
    else :
        return


def generate_respons(status, data=None, message=None):
    respons = {"status": status, "data": data, "message": message}
    return respons


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


def case_conversion(text):
    text = text.replace("_"," ")
    text = text.split(" ")
    result = ''
    for txt in text:
        x = list(txt)
        x[0] = x[0].upper()
        tmp = ''
        for i in x:
            tmp += i
        result += tmp + ' '
    return result.rstrip(" ")

def convert_new_line_to_br(text):
    try:
        return "</br>".join(text.split("\n"))
    except:
        return "</br>".join(convert(text).split("\n"))


def check_url(url):
    scheme_list = {"acap":674,"afp":548,"dict":2628,"dns":53,"file":None,"ftp":21,"git":9418,"gopher":70,"http":80,"https":443,"imap":143,"ipp":631,"ipps":631,"irc":194,"ircs":6697,"ldap":389,"ldaps":636,"mms":1755,"msrp":2855,"msrps":None,"mtqp":1038,"nfs":111,"nntp":119,"nntps":563,"pop":110,"prospero":1525,"redis":6379,"rsync":873,"rtsp":554,"rtsps":322,"rtspu":5005,"sftp":22,"smb":445,"snmp":161,"ssh":22,"steam":None,"svn":3690,"telnet":23,"ventrilo":3784,"vnc":5900,"wais":210,"ws":80,"wss":443,"xmpp":None}
    
    url_split = urlparse(url)
    if url_split.scheme and not url_split.netloc:
        if url_split.scheme not in list(scheme_list.keys()):
            return 'http://'+url
    else :
        return url


def calculate_cycle(total_run,concurrency):
    cycle = math.ceil(total_run/concurrency)
    remainder = total_run % concurrency
    
    return cycle,remainder