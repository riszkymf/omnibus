# Execution and Commands

Currently, there are two commands to execute omnibus, namely : run and cov.


### Run

Used to test remote Rest API, hence this command wont report any test coverage. 

```
omnibus run [FILE] [options] [-r|-c|-f]
```

#### Options :

- #### [-r, --requests]:
    Pretty self explanatory, running test using requests

- #### [-c, --curl]:
    Running test using curl

- #### [-f, --flask]:
    Testing local or remote flask application. This is the default settings of omnibus.

- #### [-m, --mock]:
    Use a yaml or json file as mock data for test. Very helpful if your test is using a lot of mock data

- #### [-p, --print]:
    Print response's headers and body

- #### [--body]:
    Only print response's body

- #### [--head]:
    Only print response's head

- #### [-i, --interactive]:
    Run test in interactive mode

- #### [--ignore]:
    Ignore tests file or folders.

- #### [--report REPORT]:
    Report Test Result in HTML or XML

- #### [--pm]:
    Run test using postman json file




### Cov

Testing your local Rest API using flask and report the coverage.

```
omnibus cov [FILE] [options]
```

#### Options :

- #### [-m, --mock]:
    Use a yaml or json file as mock data for test. Very helpful if your test is using a lot of mock data

- #### [-p, --print]:
    Print response's headers and body

- #### [--pb]:
    Only print response's body

- #### [--ph]:
    Only print response's head

- #### [-i, --interactive]:
    Run test in interactive mode

- #### [--ignore]:
    Ignore tests file or folders.

- #### [--source]:
    A list of packages or directories of code to be measured. Can be configured in .coveragec. For further information, [see coverage documentation](https://coverage.readthedocs.io/en/coverage-4.3.4/config.html)

- #### [--include]:
    Include only files whose paths match one of these patterns. Accepts shell-style wildcards, which must be quoted. Can be configured in .coveragec. For further information, [see coverage documentation](https://coverage.readthedocs.io/en/coverage-4.3.4/config.html)

- #### [--omit]:
    Omit files whose paths match one of these patterns. Accepts shell-style wildcards, which must be quoted. Can be configured in .coveragec. For further information, [see coverage documentation](https://coverage.readthedocs.io/en/coverage-4.3.4/config.html)

- #### [-L, --pylib]:
    Measure coverage inside Python library. Default is False.

- #### [--rcfile]:
    Specify configuration file. Default is '.coveragec', 'setup.cfg', and 'tox.ini' 

- #### [--ignore-errors]:
    Ignore errors while reading source files.

- #### [--report]:
    Specify report output (HTML or XML). Default is HTML.

- #### [--dir]:
    Directory of output files. Default is htmlcov.

- #### [--sv]:
    Save coverage data to file, example 'savedat.coverage. Default is .coverage

- #### [--rep-file]:
    Write summary report to a text file.
