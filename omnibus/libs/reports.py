import json

from lxml import etree



class Report(object):

    def __init__(self):
        self.results = list()
        self.reports = list()
        self.passed = False

def get_xml(item):
    
    if isinstance(item,tuple):
        result = etree.Element(item[0])
        if item[1]:
            if len(item[1]) > 1 and (isinstance(item[1][0],str) or isinstance(item[1][0],int)):
                txt = ""
                for i in item[1]:
                    txt += str(i) + ", "
                txt = txt.rstrip(', ')
            else:
                txt = ""
                if isinstance(item[1][0],str):
                    txt  = item[1][0]
                elif isinstance(item[1][0],int):
                    txt = str(item[1][0])
                elif isinstance(item[1][0],dict):
                    txt = str(item[1][0])
                elif isinstance(item[1][0],tuple):
                    for key,val in item[1]:
                        # tmp_el = etree.Element(key)
                        # tmp_el.text = str(val)
                        # result.append(tmp_el)
                        result.attrib[key] = val
            result.text = txt
            result = [result]
        elif isinstance(item,dict) :
            result = list()
            for key,val in item.items():
                el = etree.Element(key)
                el.text = str(val)
                result.append(el)
        return result


