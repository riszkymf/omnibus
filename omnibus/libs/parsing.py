import os
import sys
import string
from .util import generate_respons, convert


def safe_to_json(in_obj):
    """ Safely get dict from object if present for json dumping """
    if isinstance(in_obj, bytes):
        return convert(in_obj)
    if hasattr(in_obj, "__dict__"):
        return in_obj.__dict__
    try:
        return str(in_obj)
    except:
        return repr(in_obj)


def flatten_dictionaries(input):
    output = dict()
    try:
        if isinstance(input, list):
            for map in input:
                output.update(map)
        else:  # Not a list of dictionaries
            output = input
    except Exception as e:
        return generate_respons(False, None, str(e))
    else:
        return generate_respons(True, output)


def lowercase_keys(input_dict):
    if not isinstance(input_dict, dict):
        return generate_respons(False, input_dict, "Data is not dict type")
    safe = dict()
    for key, value in input_dict.items():
        safe[str(key).lower()] = value
    return generate_respons(True, safe)


def safe_to_bool(input):
    """ Safely convert user input to a boolean, throwing exception if not boolean or boolean-appropriate string
      For flexibility, we allow case insensitive string matching to false/true values
      If it's not a boolean or string that matches 'false' or 'true' when ignoring case, throws an exception """
    if isinstance(input, bool):
        return input
    elif isinstance(input, basestring) and input.lower() == u"false":
        return False
    elif isinstance(input, basestring) and input.lower() == u"true":
        return True
    else:
        raise TypeError("Input Object is not a boolean or string form of boolean!")


def safe_substitute_unicode_template(templated_string, variable_map):
    return string.Template(templated_string).safe_substitute(variable_map)

def initialize(file=None):
    obj_data = utils.yaml_parser(file)
    class_property = dict(obj_data['class']['properties'])
    class_obj_i = obj_data['class']['object']

    c_params = ''
    try:
        class_propertis = class_property['argument'];
    except Exception as e:
        class_propertis = None

    if class_propertis:
        for cl in class_propertis:
            arg_val = class_propertis[cl]['value']
            try:
                config = class_propertis[cl]['config']
            except Exception as e:
                config = None
            if config:
                if config['specified'] == False:
                    c_params += "'"+arg_val+"',"
                else:
                    c_params += cl+"='"+arg_val+"',"
            else:
                c_params += "'"+arg_val+"',"
        c_params = "("+c_params[:-1]+")"
    else:
        c_params = "()"

    class_obj = class_obj_i+c_params

    function_name = obj_data['function']['name']
    try:
        function_property = dict(obj_data['function']['parameters'])
    except Exception as e:
        function_property=None

    if function_property:
        fn_params = ''
        for fn in function_property:
            fn_arg_val = function_property[fn]['value']
            try:
                config_fn = class_propertis[cl]['config']
            except Exception as e:
                config_fn = None
            if config_fn:
                if config['specified'] == False:
                    fm_params += "'"+fn_arg_val+"',"
                else:
                    fn_params += fn+"='"+fn_arg_val+"',"
            else:
                fn_params += "'"+fn_arg_val+"',"
        fn_params = "("+fn_params[:-1]+")"
    else:
        fn_params = "()"

    function_name = function_name+fn_params
    exec_function = 's3.'+function_name

    status_exec = ''
    try:
       s3 = exe.command_class(class_obj)
       exe.command_execute(exec_function)
    except Exception as e:
        status_exec = str(e)
    else:
        status_exec = True

    print("Client Exec : "+class_obj)
    print("Function Exec : "+exec_function)
    print("Error Execute : "+status_exec)
    # output_param = dict(obj_data['output']['parameters'])
    # for out in output_param:
    #     obj =