import json

from xml.etree import ElementTree as ET
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, Comment, tostring




class Report(object):

    def __init__(self):
        self.results = list()
        self.reports = list()
        self.passed = False


def generate_xml_element(element):
    """ Processing Request and Response report """
    element_key = dict()
    for key,value in element:
        element_key[key] = ET.Element(key)
        if isinstance(value[0],tuple):
            for i,j in value:
                element_key[i] = ET.SubElement(key,i)
                element_key[i].text = j
        elif isinstance(value[0],dict):
            for i,j in value.items():
                element[i] = ET.SubElement(key,i)
                element_key[i].text = j
        elif isinstance(value[0],str):
            element_key[key].text = value          

    return element_key


def change_tuples_valtype(data):
    " Tuple must be in format (key,value) "
    new = list()
    for key,value in data:
        if not isinstance(value,list):
            value = [value]
        new.append((key,value))
    return new
