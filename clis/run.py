import os
import shutil
import yaml

from libs.util import ROOT_PATH,load_yaml,generate_file
from libs.content_parser import run_testsets,run_benchmarksets,parse_file
from docopt import docopt
from .base import Base
from termcolor import colored



class Run(Base):
    """
    Usage:
        run blackbox -f FILE [options]
        run benchmark -f FILE [options]
        run -h

    Options:
    -h --help               Print Usage
    -f FILENAME             Test File Configuration
    -d DUMPFILE             Set Dump Location
    """

    def execute(self):

        HOME = os.path.expanduser("~")
        ASSETS_PATH = os.path.join(ROOT_PATH,"templates/src")

        if not self.args['-d']:
            DUMP_LOCATION = os.path.join(HOME,'omnibus_report')
        else:
            DUMP_LOCATION = os.path.join(os.getcwd(),self.args['-d'])

        if self.args['benchmark']:
            action = "benchmark"
        elif self.args['blackbox']:
            action = "blackbox"

        FILE_LOCATION = os.path.join(os.getcwd(),self.args['-f'])
        filename = FILE_LOCATION.split("/")[-1]
        filename = filename.split(".")[0]

        try:
            config = load_yaml(FILE_LOCATION)
            if not isinstance(config,list):
                raise ValueError("Wrong YAML Configuration")
        except FileNotFoundError:
            print(colored("File not found: {}".format(FILE_LOCATION),"red"))
            exit()
        except Exception as e:
            print(colored(str(e),"red"))
            exit()

        if not os.path.exists(DUMP_LOCATION):
            try:
                print(colored("Creating directory {}".format(DUMP_LOCATION),"yellow"))
                os.mkdir(DUMP_LOCATION)
            except Exception as e:
                print(colored(str(e),"red"))
                exit()

        try:
            print(colored("Creating reports assets .....","yellow"))
            shutil.copytree(ASSETS_PATH,os.path.join(DUMP_LOCATION,"src"))
        except FileExistsError:
            pass
        except Exception as e:
            print(colored(str(e),"red"))
            exit()

        test_configs = parse_file(config,FILE_LOCATION)
        print(action)
        if action == 'benchmark':
            fail,report,html = run_benchmarksets(test_configs)
        elif action == 'blackbox':
            fail,report,html = run_testsets(test_configs)

        dump_file = os.path.join(DUMP_LOCATION,"{}.html".format(filename))
        try:
            generate_file(dump_file,html)
        except Exception as e:
            print(colored(str(e),"red"))
            exit()
        else:
            print(colored("Test Finished, Report is written on : {}".format(dump_file),"green"))


        
