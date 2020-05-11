from jinja2 import Template, FileSystemLoader, Environment
import os,pathlib,pprint,json

CWD = pathlib.Path(__file__).parent.parent
template_path = os.path.join(CWD,'templates')
blocks_path = os.path.join(template_path,'blocks')

pp = pprint.PrettyPrinter()


def write_file(text):
    with open(os.path.join(template_path,'test-tmplt.html'),"w+") as f:
        f.write(text)
                
def get_jinja_template(file):
    jinja_folder = 'blocks/{}'.format(file)
    return os.path.join(template_path,jinja_folder)

def get_css():
    css_dir = os.path.join(template_path,'src/css')
    css = os.listdir(css_dir)
    return css

def get_js():
    js_dir = os.path.join(template_path,'src/js')
    js = os.listdir(js_dir)
    return js

class JinjaHandler(object):
    raw_reports = list()
    rendered_report = None

    def __init__(self,testsets_name,success_rate,raw_reports=list()):
        self.raw_reports = raw_reports
        file_loader = FileSystemLoader(blocks_path)
        env = Environment(loader=file_loader)
        template = env.get_template('child-content.jinja')
        env = self.register_jinja_filters(env)
        self.template = template
        self.env = env
        self.testsets_name = testsets_name
        self.success = success_rate

    def sort_js(self,js_lists=list()):
        indices = ['jquery','bootstrap']
        sorted_scripts = list()
        while js_lists:
            for index in indices:
                for js in js_lists:
                    if index in js:
                        sorted_scripts.insert(len(sorted_scripts),js)
                        js_lists.remove(js)
                        break
            sorted_scripts.extend(js_lists)
            js_lists = list()
        return sorted_scripts

    def convert_report(self,raw_reports=list()):
        converted_reports = list()
        
    def build_jinja(self):
        stylesheet = get_css()
        scripts = self.sort_js(get_js())
        test_reports = self.raw_reports
        print("============================= REPORTS =============================")
        for i in test_reports:
            for key,val in vars(i).items():
                print(key," : ",val)
        test_details = {"name": self.testsets_name, "success": self.success}
        rendered_report = self.template.render(stylesheet=stylesheet,
                                        scripts=scripts,
                                        test=test_details,
                                        test_reports=test_reports)
        return rendered_report


    def _jinja_normalize_false_value__(self,value):
        try:
            newvalue = json.loads(value)
        except Exception:
            newvalue = value
        else:
            value = newvalue
        if not bool(value):
            return False
        elif not value:
            return False
        else:
            return True

    def _jinja_normalize_value(self,key,value):
        if key == 'response_headers':
            result = dict()
            for key,val in value:
                result[key] = val
            return pp.pformat(result)
        else:
            return value

    def register_jinja_filters(self,env):
        env.filters['normalize_false'] = self._jinja_normalize_false_value__
        env.filters['normalize_value'] = self._jinja_normalize_value
        return env