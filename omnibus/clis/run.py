from docopt import docopt
from omnibus.libs.util import collect_file,load_yaml,load_json
from omnibus.libs.content_parser import parse_file,run_testsets
from omnibus.libs import parsing
import os
from .base import Base

class Run(Base):
    """
    Usage:
        run (FILE) [options]

    Options:
    -h --help                       Print Usage
    -r --requests                   Test REST Endpoint using Requests
    -c --curl                       Test REST Endpoint using curl(Not implemented)
    -f --flask                      Test RESTful Flask Endpoint
    -u --url                        Global URL value
    FILE                            Test File or Folder
    -m --mock MOCK_FILE             Mock Data for test, must be yaml or json dictionary
    -p --print                      Print respons' headers and bodies
    --body                          Only print body
    --head                          Only print head
    -d --dump                       Dump Log
    -i --interactive                Interactive Mode
    """

    is_flask = True         #Default flask app
    is_request = False   
    is_curl    = False
    is_file = False
    is_dir = False
    url = None
    print_bodies = False
    print_headers = False
    is_dumped = False
    interactive = False
    is_remote = False

    def execute(self):
        print(self.args)
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
                return 0
        else :
            self.is_dir = False
            self.is_file = True
            f_tree =  self.args['FILE'].split('/')[-1]
            if not f_tree.startswith('test_'):
                print("Filename must be in 'test_{}' format".format(self.args['FILE']))
                return 0
            else:
                files.append(self.args['FILE'])
        if self.args['--requests']:
            self.is_request = True
            self.is_remote = True
        elif self.args['--flask']:
            self.is_flask = True
        elif self.args['--curl']:
            self.is_curl = True

        if self.args['--url']:
            self.url = self.args['URL']

        if self.args['--print']:
            if self.args['--body']:
                self.print_bodies = True
            if self.args['--head']:
                self.print_headers = True
            else:
                self.print_headers = True
                self.print_bodies = True
        else:
            if self.args['--body']:
                self.print_bodies = True
            if self.args['--head']:
                self.print_headers = True
        
        if self.args['--interactive']:
            self.interactive = True

        if self.args['--mock']:
            f_name = self.args['MOCK_FILE']
            acceptable_mock = ['json','yaml','yml']
            if f_name.split('.')[1].lower() not in acceptable_mock:
                print("Mock Data File must be json or yaml file type")
                f_name = None
            else:
                ext = f_name.split('.')[1].lower()
                if ext == 'json':
                    mock_vars = load_json(f_name)
                else:
                    mock_vars = load_yaml(f_name)
                    mock_vars = parsing.lowercase_keys(parsing.flatten_dictionaries(mock_vars)['data'])['data']
        else:
            mock_vars = None

        if self.args['--dump']:
            self.is_dumped = True

        for f in files:
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
                t.config.is_dumped = self.is_dumped
                t.config.is_curl = self.is_curl
                t.config.is_request = self.is_request
                t.config.is_remote = self.is_remote
            failure = run_testsets(test)
        