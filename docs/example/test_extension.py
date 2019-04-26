from omnibus.libs import validators
from omnibus.libs import generator
import random

from omnibus.libs.six import text_type,binary_type



### GENERATOR EXAMPLE

def factory_choice_generator(values):
    """ Return a generator that picks values from a list randomly """

    def choice_generator():
        my_list = list(values)
        rand = random.Random()
        while(True):
            yield random.choice(my_list)
    return choice_generator

def parse_choice_generator(config):
    """ Parse choice generator """
    vals = config['values']
    if not vals:
        raise ValueError('Values for choice sequence must exist')
    if not isinstance(vals,list):
        raise ValueError('Values must be a list of entries')
    return factory_choice_generator(vals)()






# Example Validators

class ContainsValidator(validators.AbstractValidator):
    contain_string = None

    def validate(self,body=None,headers=None,context=None):
        if isinstance(body,binary_type) and isinstance(self.contain_string,str):
            result = self.contain_string.encode('utf-8') in body
        else:
            result = self.contain_string in body
        if result:
            return True
        else:
            message = "Request body did not contain string: {}".format(self.contain_string)
            return validators.Failure(message=message,details=None,validator=self)

    @staticmethod
    def parse(config):
        if not isinstance(config, str):
            raise TypeError("Contains input must be a simple string")
        validator = ContainsValidator()
        validator.contains_string = config
        return validator

VALIDATORS = {'contains': ContainsValidator.parse}
