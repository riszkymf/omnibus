# Writing Test File

Currently omnibus only supports test files in yaml and Postman JSON. Basically test files is divided into two sections : Configuration and tests. Test files must be written in **test_yourtestname.yml** format.

---------------------
### Configuration :

There can only be one configuration per test file. Test configuration will set your global url, global endpoint, REST API location , binding variables, set generator, and headers. 

```yaml
- config:
  - desc: Configuration for Test Set
  - testset: Basic test
  - url: "http://127.0.0.1:5000"
  - endpoint: '/login'
  - headers: {'Content-Type' : 'application/json'}
  - generators: 
    - id: { type: generator_type, start: starting value}
  - flask: { path: app.module , name: create_app}
  - variable_binds: {'variable': 'value.com'}
  - expected_status: [200,205]
  - authorization: {basic: {'username': 'your_username','password':'your_password'}}
```
Notes:
- Variables that is written in configuration will be overridden if you write it in test section. For example if you write endpoint twice,  '/login' and '/logout' in configuration and test section  respectively, your test will use '/logout' as endpoint.

- flask configuration is similar as importing your flask application shown below:
```python
from path import name
### From the example 
from app.module import create_app
```
-----------------------
### Test Structure
Test structure is where you write your test data that will be executed. There are several features that is currently available in omnibus to help you test your Rest API.

- Generator Binder : Bind generator from test configuration
- Variable Binder : Binding variable to be used on other test
- Extractor : Extract data from test result.
- Validators : Validate test result.
- Templating : Template test variables

```yaml
- test: 
  - name: "TestName"
  - endpoint: "/endpoint"
  - method: "GET"
  - group: #test group
  - body: #Body
  - generator_binds: #Bind generator 
  - headers: #headers
  - extract_binds: 
      - # extract test result
      - # extract another test result
  - validators:
      - # your assertion
      - # your assertion
  - expected_status: [200] # A list of your expected result's status code. If not written, default is 200
```

- Test group is used during report (test report, not coverage). FOr example, a test file with two different test groups will generate a report like this

```raw
Test Group Group_1 , on test_generator.yml, SUCCEEDED: 2/2 Tests Passed!
Test Group Group_2 , on test_generator.yml, SUCCEEDED: 3/3 Tests Passed!
```

- To use generator from configuration, generator have to be binded using generator_binds

----------------------------

For further information on generators, binders, validators and others, see [documentation](features.md)

- [Back to Readme](../README.md)