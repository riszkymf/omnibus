from docopt import docopt
import os
import sys
from coverage import Coverage

from omnibus.libs.util import load_yaml,load_json,get_all,get_path,get_path_files
from omnibus.libs.content_parser import parse_file,run_testsets
from omnibus.libs import parsing

from.base import Base


class Cov(Base):
    """
    Usage:
        cov (FILE) [options]

    Options:
    -h --help                       Show this help message
    FILE                            Your test file(s)
    -u, --url URL                   Global URL value
    -m, --mock MOCK_FILE            Mock Data for test, must be yaml or json dictionary
    -p, --print                     Print respons
    --pb                            Only print respons' body
    --ph                            Only print respons' head
    -i, --interactive               Enter Interactive Mode
    --omit=PAT1,PAT2,...            Omit files whose paths match one of these patterns. 
                                    Accepts shell-style wildcards, which must be quoted.
    --include=PAT1,PAT2,...         Include only files whose paths match one of these patterns. 
                                    Accepts shell-style wildcards, which must be quoted.
    --source=SRC1,SRC2,...          A list of packages or directories of code to be measured
    -L, --pylib                     Measure coverage inside Python library. Default is False
    --rcfile=RCFILE                 Specify configuration file. Default is '.coveragec', 'setup.cfg', and 'tox.ini' 
    --ignore-errors                 Ignore errors while reading source files.
    --report REPORT                 Specify report output (HTML or XML). Default is HTML
    --dir DIR                       Directory of output files. Default is htmlcov.
    --ignore IGDIR                  Test directory to be ignored.
    --sv DATA_FILE                  Save coverage data to file for later use, example : 'savedat.coverage' .Default is .coverage 
    --rep-file FILE                 Write summary report
    """

    dir_out = None
    f_conf = None
    f_omit = None
    f_incl = None
    f_ignore = list()
    f_mock = None
    f_tests = list()
    d_mock = None
    url = None
    print_bodies = False
    print_headers = False
    interactive = False
    err = False
    savedat = None
    suffix = None
    source_list = None

    def execute(self):

        self.dir_out = self.args['--dir']
        self.err = self.args['--ignore-errors']
        self.url = self.args['--url']
        self.interactive = self.args['--interactive']
        
        test_struct = list()
        test_paths = list()
        cwd = os.getcwd()

        if self.args['--ignore']:
            self.args['--ignore'] = get_path(cwd,self.args['--ignore'])
            self.f_ignore = [self.args['--ignore']]
        else:
            self.f_ignore = list()
            
        path = get_path(cwd,self.args['FILE'])
        if os.path.isdir(path):
            self.is_dir = True
            self.is_file = False
            self.f_tests = get_all(path,self.f_ignore)
            if len(self.f_tests) == 0:
                print("No test file is found")
                return 0
        else:
            self.is_dir = False
            self.is_file = True
            f_tree = self.args['FILE'].split('/')[-1]
            if not f_tree.startswith('test_'):
                print("Filename must be in 'test_{}' format".format(self.args['FILE']))
                return 0
            else:
                if self.args['FILE'] in self.f_ignore:
                    print("Ignored file and test file is the same file")
                    return 0
                else:
                    self.f_tests.append(path)

        if self.args['--print']:
            if self.args['--pb']:
                self.print_bodies = True
            if self.args['--ph']:
                self.print_headers = True
            else:
                self.print_headers = True
                self.print_bodies = True

        if self.args['--interactive']:
            self.interactive = True

        if self.args['--mock']:
            self.f_mock = self.args['MOCK_FILE']
            acceptable_mock = ['json','yaml','yml']
            if self.f_mock.split('.')[1].lower() not in acceptable_mock:
                print("Mock Data File must be json or yaml")
                self.f_mock = None
            else:
                ext = self.f_mock.split('.')[1].lower()
                if ext == 'json':
                    self.d_mock = load_json(self.f_mock)
                else:
                    self.d_mock = load_yaml(self.f_mock)
                    self.d_mock = parsing.lowercase_keys(parsing.flatten_dictionaries(self.d_mock)['data'])['data']
        
        if self.args['--sv']:
            self.savedat = self.args['--sv'].split('.')
            if len(self.savedat) == 1:
                self.suffix = True
                self.savedat = self.savedat[0]
            elif len(self.savedat) == 2:
                self.suffix = self.savedat[1]
                self.savedat = self.savedat[0]
        
        if self.args['--rcfile']:
            self.f_conf = get_path(cwd,self.args['--rcfile'])
            
        if self.args['--source']:
            self.source_list = get_path_files(self.args['--source'])

        if self.args['--omit']:
            self.f_omit = get_path_files(self.args['--omit'])
        
        if self.args['--include']:
            self.f_incl = get_path_files(self.args['--include'])

        if self.args['--rep-file']:
            report_file = get_path_files(self.args['--rep-file'])
            report_file = report_file[0]
        else:
            report_file = None
        
        if self.dir_out:
            self.dir_out = get_path_files(self.dir_out)

        cov = Coverage(
            data_file=self.savedat,
            data_suffix=self.suffix,
            cover_pylib=self.args['--pylib'],
            config_file=self.f_conf,
            source = self.source_list,
            omit=self.f_omit,
            include=self.f_incl
        )
        
        cov.start()

        for f in self.f_tests:
            if load_yaml(f):
                test_struct.append(load_yaml(f))
                test_paths.append(os.path.dirname(f))
            else:
                print("\033[93m Warning: Test file \033[4m{}\033[0m \033[93m and is skipped.\033[0m".format(f.split("/")[-1]))

        tests = list()

        for t,p,f in zip(test_struct,test_paths,self.f_tests):
            tests.append(parse_file(t,f,p,vars=self.d_mock,global_url=self.url))

        for test in tests:
            for t in test:
                t.config.print_bodies = self.print_bodies
                t.config.print_headers = self.print_headers
                t.config.interactive = self.interactive
            failures = run_testsets(test)

        cov.stop()
        if self.args['--sv']:
            cov.save()
        print("=============================================================")
        print("                          REPORT                             ")
        print("=============================================================")

        cov.report(ignore_errors=self.err, file=report_file)

        report = self.args['--report']
        if report:
            if report.lower() == 'html' :
                cov.html_report(directory=self.dir_out[0],ignore_errors=self.err )
            elif report.lower() == 'xml':
                cov.xml_report(outfile=self.dir_out[0],ignore_errors=self.err)
            
        sys.exit(failures)