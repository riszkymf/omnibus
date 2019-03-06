from docopt import docopt
from omnibus.libs.util import collect_file,load_yaml,load_json
from omnibus.libs.content_parser import parse_file,run_testsets
from omnibus.libs import parsing
import os
from .base import Base

class Run(Base):
    """
    Usage:
        run (FILE) [-r | -c] [-u URL] [-m MOCK_FILE] [-p[--body|--head]] [-i]

    Options:
    -h --help                       Print Usage
    -r --requests                   Test REST Endpoint using Requests
    -c --curl                       Test REST Endpoint using curl(Not implemented)
    -u --url                        Global URL value
    FILE                            Test File or Folder
    -m --mock MOCK_FILE             Mock Data for test, must be yaml or json dictionary
    -p                              Print respons' headers and bodies
    --body                          Only print body
    --head                          Only print head
    -i --interactive                Interactive Mode
    """

    is_request = True   #Default using requests
    is_curl    = False
    is_file = False
    is_dir = False
    url = None
    print_bodies = False
    print_headers = False
    interactive = False

    def execute(self):
        files = list()
        struct = list()
        paths = list() 
        cwd = os.getcwd()
        if os.path.isdir(os.path.join(cwd,self.args['FILE'])):
            self.is_dir = True
            self.is_file = False
            files = collect_file(self.args['FILE'])
            if len(files) == 0 : 
                print("No test file is found")
        else :
            self.is_dir = False
            self.is_file = True
            f_tree =  self.args['FILE'].split('/')[-1]
            if not f_tree.startswith('test_'):
                print("Filename must be in 'test_{}' format".format(self.args['FILE']))
                return 0
            else:
                files.append(self.args['FILE'])
        
        if self.args['--curl']:
            self.is_curl = True
            self.is_request = False

        if self.args['--url']:
            self.url = self.args['URL']

        if self.args['-p']:
            if self.args['--body']:
                self.print_bodies = True
            elif self.args['--head']:
                self.print_headers = True
            else:
                self.print_headers = True
                self.print_bodies = True
        
        if self.args['--interactive']:
            self.interactive = False

        if self.args['--mock']:
            f_name = self.args['MOCK_FILE']
            acceptable_mock = ['json','yaml','yml']
            if f_name.split('.')[1].lower() not in acceptable_mock:
                print("Mock Data File must be json or yaml file type")
            else:
                ext = f_name.split('.')[1].lower()
                if ext == 'json':
                    mock_vars = load_json(f_name)
                else:
                    mock_vars = load_yaml(f_name)
                    mock_vars = parsing.lowercase_keys(parsing.flatten_dictionaries(mock_vars)['data'])['data']
        else:
            mock_vars = None

        for f in files:
            print(f)
            struct.append(load_yaml(f))
            paths.append(os.path.dirname(f))
        
        tests = list()

        for t,p,f in zip(struct,paths,files):
            tests.append(parse_file(t,f,p,vars=mock_vars,global_url=self.url))
            

        for test in tests:
            for t in test:
                t.config.print_bodies = self.print_bodies
                t.config.print_headers = self.print_headers
                t.config.interactive = self.interactive
            failure = run_testsets(test)
        