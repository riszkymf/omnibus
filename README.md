# omnibus

Omnibus is a python powered API testing tools where all the testing is written on YAML based on [pyresttest](https://github.com/svanoort/pyresttest).

## Installation
1. Clone this repo into your machine using 
```
git clone https://github.com/riszkymf/omnibus
```
2. Install requirements
```
pip install -r requirements.txt
```

now you can run the omnibus cli to start your test.


## Test Configuration
Here is a test file example for a reqres endpoint.
## Example
```yaml
- config:
  - desc: Configuration for Reqres Endpoint Test
  - testset: "Reqres Endpoints"
  - url: "https://reqres.in/"
  - headers: {'Content-Type': 'application/json'}
  - variable_binds: {'firstname': 'John', 'lastname': 'Doe'}
- test: 
  - name: "TestListUsers"
  - endpoint: 'api/users?page=2'
  - method: "GET"
  - group : "Get"
  - headers: {'Content-Type': 'application/json'}
  - extract_binds: 
      - 'name' : {'jmespath' : 'data[*].first_name'}
  - validators:
      - assertTrue: {jmespath: 'data', test: exists }
      - compare: {jmespath: 'data[1].first_name', comparator: "eq", expected: 'Charles'}
- test:
  - name: "GetFailed404"
  - endpoint: 'api/unknown/23'
  - method: "GET"
  - headers: {'Content-Type': 'application/json'}
  - group: "Get"
  - expected_status: [404]
- test:
  - name: "CreateName"
  - endpoint: 'api/users'
  - method: "POST"
  - group: "Post"
  - headers: {'Content-Type': 'application/json'}
  - body: { template: '{"name": "$firstname", "job": "bard"}'}
  - expected_status: [200,201]
  - validators:
      - compare: {jmespath: 'name', comparator: "eq", expected: 'John'}
```
Creating a test file is as simple as creating a yaml file with 2 main configuration:
 - Config
 - Test
 
Where each of them will need a url (You can set a global target_url on config and endpoints on test), method, body and expected status.

Since it's based on pyresttest, for user use you can check [their documentation](https://github.com/svanoort/pyresttest/blob/master/quickstart.md)

For validation and templating you can refer to [Features](/docs/features.md)
`config` will be run once at the start of the test.

## CLI
[CLI Documentation](/docs/commands.md)
