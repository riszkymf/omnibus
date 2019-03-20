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

### 4. Extractor

Extractor is a tool to extract certain data from result's body. 