# Features

## Generators and Binding Generators
----------------

Usage: 

Generator must be declared in configuration. Then, it have to be binded in test data. Currently omnibus support multiple generators per testsets. 


```yaml
#Declaring Generator
config:
    - generator:
        - generator_name_1: { type: generator_type}
        - generator_name_2: { type: generator_type}
#Binding Generator
test:
    - generator_binds: { gen_1: generator_name_1, gen_2: generator_name_2}
```

### Generator Types:

| Description                                                    	| Generator Name  	| Required Parameter (name,type) 	| Optional Parameter (name,type,default value)                                                                                    	| Output Type 	|
|----------------------------------------------------------------	|-----------------	|--------------------------------	|---------------------------------------------------------------------------------------------------------------------------------	|-------------	|
| Integer Sequence                                               	| number_sequence 	| None                           	|  (start,integer,1) (increment,integer,1)                                                                                        	| Integer     	|
| Integer Random                                                 	| random_int      	| None                           	| None                                                                                                                            	| Integer     	|
| Text Random                                                    	| random_text     	| None                           	|  (character_set/characters, string, string.ascii_letters) (min_length, integer, 8) (max_length, integer, 8) (length, integer,8) 	| String      	|
| Choice of random values from input list                        	| choice          	| (values,list)                  	| None                                                                                                                            	| Any         	|
| Sequence of values from input list of values, looping in order 	| fixed_sequence  	| (values,list)                  	| None                                                                                                                            	| Any         	|


### Example Usage:
```yaml
#Declaring generator
- config:
    - generator:
        - id_seq: { type: number_sequence, start: 0, increment: 2 }
        - id_random: { type: random_int}
        - str_rand: { type: random_text, length: 5}
        - the_choice: { type: choice, values: ['this','is','a','test']}
        - is_yours: {type: fixed_sequence, values: [1,2,3,4]}

#Binding Generator
- test:
    - generator_binds: { ids: 'id_random', str: 'str_rand'}

```

Note that currently generator can only be used once per test (not test file). Benchmarking feature will be added

## Variable Binds
---------------------

Variable binder is a tool to bind values to variables in test file for later use. Variable binder can be used in configuration or tests.

Usage:

```yaml
- config: 
    - variable_binds: {'var_1' : 'value_1', 'var_2': 'value_2'}
## This is permitted

- test:
    - variable_binds: {'var_3' : 'value_3', 'var_4': 'value_4'}
## This is permitted too
    - body: { template: {"value" : "$var_3"}}
    - validators:
        - compare: { jmespath: 'data[0].value', comparator: 'contains', expected: { template: $var_4}}

```

- On the example above value_1 is binded to var_1, value_2 is binded to var_2, and so on.
- var_3 is used in test's body and var_4 is used as validator that compares var_4's value to extracted test's result.
- As shown above, when using binded variable, we need to use template and **'$'** before the variable's name.
- The example above is similar as:

```python
body = {"value" : 'value_3'}
assert data[0]['value'] == value_4
```

## Validators
----------------
Basically, validators are test assertion. Validators support templating and extracting test data.

There are several available validators:


### 1. Extract and Test Value
- Name: extract_test
- Description : Extract certain value from test result and test it using a function

- Arguments:
    * (extractor): Extractor used in test. See below
    * test: Test function to apply on extracted value
- Examples:
```yaml
- validators: 
  - extract_test: { jsonpath_mini: "not_exists", test: "not_exist" }
```
The validator above will check if the extracted data doesn't exist. If it does, then the test will not pass.  

- Test function:
    * exists
    * not_exists

### 2. Extract compare Test Value

- Name: comparator / compare / assertTrue
- Description: Extract and compare extracted test result to a certain value
- Arguments:
    * extractor: extractor used on test result. See below for further information.
    * comparator: Comparator used on extracted value. See table below.
    * expected: 
        * expected value (a literal)
        * a template : {template : $var}
        * an extractor definition. (Extractor binded into variable)
- Examples: 
```yaml
- validators: 
    - compare: {jsonpath_mini: "user_name", comparator: "eq", expected: "neo"}
    - compare: {jsonpath_mini: "id", comparator: 'greater_than', expected: "10"}
```

### List of Comparators

| Extractor Names               	| Description                               	| Details in f(A,B)                            	|
|-------------------------------	|-------------------------------------------	|----------------------------------------------	|
| 'count_eq','length_eq'        	| Check length extracted value              	| length(A) == B or -1 if cannot obtain length 	|
| 'lt','less_than'              	| Less than                                 	| A < B                                        	|
| 'le', 'less_than_or_equal'    	| Less than or equal to                     	| A <= B                                       	|
| 'eq','equals'                 	| Equals                                    	| A == B                                       	|
| 'str_eq'                      	| Values are equal when converted to string 	| str(A) == str(B)                             	|
| 'ne','not_equals'             	| Not equals                                	| A != B                                       	|
| 'gt', 'greater_than'          	| Greater Than                              	| A > B                                        	|
| 'ge', 'greater_than_or_equal' 	| Greater Than Or Equal To                  	| A >= B                                       	|
| 'contains'                    	| Contains                                  	| B in A                                       	|
| 'contained_by'                	| Contained By                              	| A in B                                       	|
| 'type'                        	| Type of variable                          	| A is instance of (at least on of) B          	|
| 'regex'                       	| Regex Equals                              	| A matches regex B                            	|



**********************
##  Extractor

Extractor is a tool to extract certain data from result's body. Omnibus has several extractor, namely:

### 1. Header extractor:
- Name : "header"
- Description: Extract headers' element from response

Example:
```yaml
- variable_binds:
    - p: { header: 'Content-Type'}
```
From the example above, extractor will extract content type from headers and bind it to 'p'.

### 2. Body Extractor
- Name: "raw_body"
- Description: Extracts raw body from response

Example:
```yaml
- variable_binds:
  - b: { raw_body }
```
Note that body extractor don't need any configuration to point which part of response's body that it will extract as it will bind the whole body to 'b'.

### 3. JSONpath_mini:

The basic 'jsonpath_mini' extractor provides a very limited JsonPath-like implementation to grab data from JSON, with no external library dependencies.

The elements of this syntax are a list of keys or indexes, descending down a tree, seperated by periods. Numbers are assumed to be array indices.

If you wish to return the whole object, you may use an empty "" query or "." -- this can be helpful for APIs returning an array of objects, where you want to count the number of objects returned (using countEq operator).


- Name: jsonpath_miini:
- Description: Extracts elements from json body

Example:

Given this json as response :
```json
{
    "count": 3,
    "data": [
        {
            "id_zone": "426187006277550081",
            "nm_zone": "harlem2.com",
            "state": 1
        },
        {
            "id_zone": "426187074628517889",
            "nm_zone": "harlem.com",
            "state": 1
        },
        {
            "id_zone": "428136215926702081",
            "nm_zone": "burungbetina.com",
            "state": 1
        }
    ],
    "code": 200,
    "status": "success",
    "message": "Operation succeeded"
}
```
```yaml
- variable_binds: 
    - data: { jsonpath_mini: 'jsonpath_mini syntax' }
```

JSONPATH syntax will extract data as shown below.

| JSONPATH_MINI SYNTAX     	| RESULT                                                                                                                                        	|
|--------------------------	|-----------------------------------------------------------------------------------------------------------------------------------------------	|
| data.1                   	| [{"id_zone":"426187074628517889","nm_zone":"harlem.com","state":1}]                                                                           	|
| data.1.nm_zone           	| "harlem.com"                                                                                                                                  	|
| code                     	| 200                                                                                                                                           	|
| data.0,2                 	| [{"id_zone":"426187006277550081","nm_zone":"harlem2.com","state":1}, {"id_zone":"428136215926702081","nm_zone":"burungbetina.com","state":1}] 	|
| data.0,2.nm_zone         	| ["harlem2.com","burungbetina.com"]                                                                                                            	|
| data.0,2.nm_zone,id_zone 	| ["harlem2.com","426187006277550081","burungbetina.com","428136215926702081"]                                                                  	|
| data.*.id_zone           	| ["426187006277550081","426187074628517889","428136215926702081"]                                                                              	|

Jsonpath extractor also supports templating, for example if you call:
```yaml
jsonpath_mini: { template: $call.0.nm_zone}
```
if variable call is set to 'data' , then it will extract 'harlem2.com'

For further information on jsonpath, see [documentation](https://github.com/kennknowles/python-jsonpath-rw)

### 4. JMESPATH Extractor

- Name : jmespath
- Description: The 'jmespath' extractor provides fulll                     JMESPath implementation to grab data from JSON and requires jmespath library to be available for import. Full range of JMESPath expressions is supported.

Given this JSON data:
```json
{
   "test1" : {"a": "foo", "b": "bar", "c": "baz"},
   "test2" : {"a": {"b": {"c": {"d": "value"}}}},
   "test3" : ["a", "b", "c", "d", "e", "f"],
   "test4" : {
      "a": {
        "b": {
          "c": [
            {"d": [0, [1, 2]]},
            {"d": [3, 4]}
          ]
        }
      } },
   "test5" : [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
   "test6" : {
      "people": [
         {"first": "James", "last": "d"},
         {"first": "Jacob", "last": "e"},
         {"first": "Jayden", "last": "f"},
         {"missing": "different"}
      ],
      "foo": {"bar": "baz"}
   },
   "test7" : {
      "ops": {
         "functionA": {"numArgs": 2},
         "functionB": {"numArgs": 3},
         "functionC": {"variadic": 4}
      }
   },
   "test8" : {
      "reservations": [
         { "instances": [ {"state": "running"}, {"state": "stopped"} ] },
         { "instances": [ {"state": "terminated"}, {"state": "runnning"} ] }
      ]
   },
   "test9" : [ [0, 1], 2, [3], 4, [5, [6, 7]] ],
   "test10" : { "machines": [ {"name": "a", "state": "running"}, {"name": "b", "state": "stopped"}, {"name": "c", "state": "running"} ] },
   "test11" : {
      "people": [
         { "name": "b", "age": 30, "state": {"hired": "ooo"} },
         { "name": "a", "age": 50, "state": {"fired": "ooo"} },
         { "name": "c", "age": 40, "state": {"hired": "atwork"} } ]
   } ,
   "test12" : { "myarray": [ "foo", "foobar", "barfoo", "bar", "baz", "barbaz", "barfoobaz" ] }
}
```
Query results is shown on table below.

| Query                           | Output                        |
|---------------------------------|-------------------------------|
| ```'test1.a'```                 | ```"foo"```                   |
| ```'test1.b'```                 | ```"bar"```                   |
| ```'test1.c'```                 | ```"baz"```                   |
| ```'test2.a.b.c.d'```           | ```"value"```                 |
| ```'test3[1]'```                | ```"b"``` |
|```'test4.a.b.c[0].d[1][0]'``` | ```1``` |
|```'length(test5[0:5])'``` | ```5``` |
|```'test5[1:3]'``` | ```'[1, 2]'``` |
|```'test5[::2]'``` | ```'[0, 2, 4, 6, 8]'``` |
|```'test5[5:0:-1]'``` | ```'[5, 4, 3, 2, 1]'``` |
|```'test6.people[*].first'``` | ```"['James', 'Jacob', 'Jayden']"``` |
|```'test6.people[:2].first'``` | ```"['James', 'Jacob']"``` |
|```'test6.people[*].first | [0]'``` | ```'James'``` |
|```'test7.ops.*.numArgs'``` | ```'[2, 3]'``` |
|```'test8.reservations[*].instances[*].state'``` | ```"[['running', 'stopped'], ['terminated', 'runnning']]"``` |
|```'test9[]'``` | ```'[0, 1, 2, 3, 4, 5, [6, 7]]'``` |
|```"test10.machines[?state=='running'].name"``` | ```"['a', 'c']"``` |
|```"test10.machines[?state!='running'][name, state] | [0]"``` | ```"['b', 'stopped']"``` |
|```'length(test11.people)'``` | ```3``` |
|```'max_by(test11.people, &age).name'``` | ```'a'``` |
|```"test12.myarray[?contains(@, 'foo') == `true`]"``` | ```"['foo', 'foobar', 'barfoo', 'barfoobaz']"``` |

-------------------

## Authorization

Currently Omnibus supports 4 Types of Authorization, namely : OAuth1 , Digest, Basic requests and Bearer Token

Will be implemented : Oauth2 obtains and keystone


### 1.OAuth1

- name: OAuth1
- Parameters : consumerkey,consumersecret,token,tokensecret

Example
```yaml
- authorization: { oauth1: {'consumerkey': 'your_key', 'consumersecret':'your_secret', 'token' : 'your_token', 'tokensecret': 'your_token_secret'}}
```

### 2.Digest
 - name: digest
 - parameters: username,password

 Example:
 ```yaml
- authorization: { digest: { 'username': 'username', 'password': 'password'}}
 ```

 ### 3.Basic
 - name: basic
 - parameters: username,password

 Example:
 ```yaml
 - authorization: { basic: { 'username' : 'username', 'password' : 'password' }}
 ```

### 4. Bearer Token
- name : bearer
- parameters: token

Example:
```yaml
- authorization: { bearer: {'token' : 'Bearer yourtoken' } }
```

- [Back to Readme](../README.md)