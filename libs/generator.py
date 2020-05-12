import random
import string
import os
import sys
import json

from libs import parsing
from .parsing import flatten_dictionaries, lowercase_keys, safe_to_bool


INT32_MAX_VALUE = 2147483647

CHARACTER_SETS = {
    "ascii_letters": string.ascii_letters,
    "ascii_lowercase": string.ascii_lowercase,
    "ascii_uppercase": string.ascii_uppercase,
    "digits": string.digits,
    "hexdigits": string.hexdigits,
    "hex_lower": string.digits + "abcdef",
    "hex_upper": string.digits + "ABCDEF",
    "letters": string.ascii_letters,
    "lowercase": string.ascii_lowercase,
    "octdigits": string.octdigits,
    "punctuation": string.punctuation,
    "printable": string.printable,
    "uppercase": string.ascii_uppercase,
    "whitespace": string.whitespace,
    "url.slug": string.ascii_lowercase + string.digits + "-",
    "url.safe": string.ascii_letters + string.digits + "-~_.",
    "alphanumeric": string.ascii_letters + string.digits,
    "alphanumeric_lower": string.ascii_lowercase + string.digits,
    "alphanumeric_upper": string.ascii_uppercase + string.digits,
}


def generate_ids(starting_id=1, increment=1):
    """ Return function generator for ids starting at starting_id
      Needs to be called with () to create a generator """

    def generate_started_ids():
        val = starting_id
        local_increment = increment
        while True:
            yield val
            val += local_increment

    return generate_started_ids


def generator_basic_ids():
    """ Return ids generator starting at 1"""
    return generate_ids(1)()


def generator_random_int32():
    """ Generate random int-32 signed """
    rand = random.Random()
    while True:
        yield random.randint(0, INT32_MAX_VALUE)


def factory_generate_text(
    legal_characters=string.ascii_letters, min_length=8, max_length=8
):
    def generate_text():
        local_min_len = min_length
        local_max_len = max_length
        rand = random.Random()
        while True:
            length = random.randint(local_min_len, local_max_len)
            array = [random.choice(legal_characters) for x in range(0, length)]
            yield "".join(array)

    return generate_text


def factory_fixed_sequence(values):
    def seq_generator():
        my_list = list(values)
        i = 0
        while True:
            yield my_list[i]
            i += 1
            if i == len(my_list):
                i = 0

    return seq_generator


def parse_fixed_sequence(config):
    """ Parse fixed sequence string """

    vals = config["values"]
    if not vals:
        raise ValueError(" Values must exist")
    if not isinstance(vals, list):
        raise ValueError(" Vaues must be list of entries")
    return factory_fixed_sequence(vals)()


def factory_choice_generator(values):
    """ Return generator that picks values from a list """

    def choice_generator():
        my_list = list(values)
        rand = random.Random()
        while True:
            yield random.choice(my_list)

    return choice_generator


def parse_choice_generator(config):
    """ Parse choice generator """
    vals = config["values"]
    if not vals:
        raise ValueError("Values must exist")
    if not isinstance(vals, list):
        raise ValueError("Value must be list of entries")
    return factory_choice_generator(vals)()


def factory_env_variable(env_variable):
    def return_variable():
        variable_name = env_variable
        while True:
            yield os.environ.get(variable_name)

    return return_variable


def factory_env_string(env_string):
    """ Return a generator function that uses OS expand path to expand environment variables in string """

    def return_variable():
        my_input = env_string
        while True:
            yield os.path.expandvars(my_input)

    return return_variable


def parse_random_text_generator(configuration):
    """ Parses configuration options for a random text generator """
    character_set = configuration.get(u"character_set")
    characters = None
    if character_set:
        character_set = character_set.lower()
        if character_set not in CHARACTER_SETS:
            raise ValueError(
                """ Illegal character set name, is not defined: {0}.""".format(
                    character_set
                )
            )
        characters = CHARACTER_SETS[character_set]
    else:
        characters = str(configuration.get(u"characters"))

    min_length = 8
    max_length = 8

    if configuration.get(u"min_length"):
        min_length = int(configuration.get(u"min_length"))
    if configuration.get(u"max_length"):
        max_length = int(configuration.get(u"max_length"))

    if configuration.get(u"length"):
        length = int(configuration.get(u"length"))
        min_length = length
        max_length = length

    if characters:
        return factory_generate_text(
            legal_characters=characters, min_length=min_length, max_length=max_length
        )()
    else:
        return factory_generate_text(min_length=min_length, max_length=max_length)


GENERATOR_TYPES = set(
    [
        "env_variable",
        "env_string",
        "number_sequence",
        "random_int",
        "random_text",
        "fixed_sequence",
    ]
)

GENERATOR_PARSING = {"fixed_sequence": parse_fixed_sequence}


def register_generator(typename, parse_function):
    """ Register a new generator for use in testing
      typename is the new generator type name,
      parse_function will parse a configuration object
  """
    if not isinstance(typename, str):
        raise TypeError(
            "Generator type name {0} is invalid, must be a string".format(typename)
        )
    if typename in GENERATOR_TYPES:
        raise ValueError("Generator type name {0} already exists".format(typename))
    GENERATOR_TYPES.add(typename)
    GENERATOR_PARSING[typename] = parse_function

register_generator('choice', parse_choice_generator)


def parse_generator(configuration):
    """ Parses a configuration built from yaml and returns generator.
      Configuration should be a map
  """

    configuration = lowercase_keys(flatten_dictionaries(configuration))
    gen_type = str(configuration.get(u"type"))

    if gen_type not in GENERATOR_TYPES:
        raise ValueError("Generator type given {0} is not valid".format(gen_type))

    if gen_type == u"env_variable":
        return factory_env_variable(configuration[u"variable_name"])()
    elif gen_type == "env_string":
        return factory_env_string(configuration[u"string"])()
    elif gen_type == u"number_sequence":
        start = configuration.get("start")
        increment = configuration.get("increment")

        if not start:
            start = 1
        else:
            start = int(start)

        if not increment:
            increment = 1
        else:
            increment = int(increment)
        return generate_ids(start, increment)()
    elif gen_type == "random_int":
        return generator_random_int32()
    elif gen_type == "random_text":
        return parse_random_text_generator(configuration)
    elif gen_type in GENERATOR_TYPES:
        return GENERATOR_PARSING[gen_type](configuration)
    else:
        raise Exception("Unknown generator type")

