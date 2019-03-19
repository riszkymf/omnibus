# Features

## Generators and Binding Generators
----------------

Usage: 
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

