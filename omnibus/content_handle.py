import os
import sys
from omnibus.util import convert
from omnibus.binding import *
from omnibus.parsing import *


class ContentHandler:
  content = None
  is_file = False
  is_template_path = False
  is_template_content = False

  def is_dynamic(self):
    return self.is_template_path or self.is_template_content

  def get_content(self,context=None):

    if self.is_file:
      path = self.content
      if self.is_template_path and context:
        path = string.Template(path).safe_substitute(
          context.get_values())
        data = None
        with open(path,'r') as f:
          data = f.read()
        
        if self.is_template_content and context:
          return string.Template(data).safe_substitute(context.get_values())
        else:
          return data
    else:
      if self.is_template_content and context:
        return safe_substitute_unicode_template(self.content, context.get_values())
      else :
        return self.content

  def create_noread_version(self):
    """ Read file content if it is static and return content handler with no I/O """
    if not self.is_file or self.is_template_path:
      return self
    output = ContentHandler()
    output.is_template_content = self.is_template_content
    with open(self.content,'r') as f:
      output.content = f.read()
    return output

  def setup(self,d_input,is_file=False,is_template_path=False,is_template_content=False):
    if not isinstance(d_input,str):
      raise TypeError("Input is not String")
    if is_file:
      d_input = os.path.abspath(d_input)
    self.content = d_input
    self.is_file = is_file
    self.is_template_content = is_template_content
    self.is_template_path = is_template_path

  @staticmethod
  def parse_content(node):
    
    output = ContentHandler()
    is_template_content = False
    is_template_path = False
    is_file = False
    is_done = False

    while (node and not is_done):
      print(" ===> ",type(node))
      print(" +++ ", node)
      if isinstance(node,str):
        output.content = node
        print("is_template_content",'=',is_template_content)
        print("is_template_path",'=',is_template_path)
        print("is_template_file",'=',is_template_file)
        output.setup(node,is_file=is_file,is_template_path=is_template_path,
        is_template_content=is_template_content)
        return output
      elif not isinstance(node,dict) and not isinstance(node,list):
        raise TypeError(
          """ Content must be string, list, or dictionary """)
      
      is_done = True
      
      flat = lowercase_keys(node)['data']
      for key,value in flat.items():
        if key == u'template':
          print("--CHECKPOINT-1")
          if isinstance(value,str):
            if is_file:
              value = os.path.abspath(value)
            output.content = value
            is_template_content = is_template_content or not is_file
            output.is_template_content = is_template_content
            output.is_template_path = is_file
            output.is_file = is_file
            return output
          else:
            print("--CHECKPOINT-2")
            is_template_content = True
            node = value
            is_done = False
            break
        
        elif key == 'file':
          if isinstance(value,str):
            output.content = os.path.abspath(value)
            output.is_file = True
            output.is_template_content = is_template_content
            return output
          
          else:
            is_file = True
            node = value
            is_done = False
            break

    print("\nHOHO\n")
    #raise Exception("Invalid configuration of content")


