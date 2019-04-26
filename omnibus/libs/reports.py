import json
import pprint
import os
from lxml import etree
from copy import copy
from omnibus.libs.util import *
from omnibus.libs.parsing import safe_to_json
from yattag import Doc

test_files = list()
failure_report = list()

class Report(object):


    def __init__(self,report=None):
        if not report:
            self.results = list()
            self.reports = list()
            self.passed = False

    def __str__(self):
        return json.dumps(self, default=safe_to_json)


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


def generate_report_config(report):

    def config_report(reportdata):
        content = "<tbody>"
        trow = ''
        for data in reportdata:
            data_rep = dict()
            for key,val in data.reports:
                data_rep[key] = val
            if data.passed[0]:
                tclass = ""
            else:
                tclass = "table-danger"
            trow += '<tr class = "{} clickable-row" data-url="#{}">'.format(tclass,data_rep['test_name'][0])
            td = "<td>{}</td>".format(data_rep['test_name'][0])
            td += "<td>{}</td>".format(data_rep['group'][0])
            td += "<td>{}</td>".format(data_rep['method'][0])
            td += "<td>{}</td>".format(data_rep['url'][0])
            if data.passed[0]:
                passed = "<b style='color:#016613;'>Passed</b>"
            else:
                passed = "<b style='color:#8c0c01;'>Failed</b>"
            td += "<td>{}</td>".format(passed)
            trow += td+"</a></tr>"
        content += trow + "</tbody>"
        return content
    text = config_report(report)

    myconfigreport = """
    <div class="col-md-10 offset-md-1">
    <table id="sumTable" class="table table-sm table-list-search">
        <thead>
            <tr>
                <th>Test Name</th>
                <th>Test Group</th>
                <th>Method</th>
                <th>Endpoint</th>
                <th>Status</th>
            </tr>
        </thead>
        {}
    </table></div>""".format(text)
    return myconfigreport


def group_assign(myreport):
    """ Assign test result by its group. Returns a dict of : {group : reports}"""
    group = dict()
    for report in myreport:
        for key,val in report.reports:
            if key.lower() == 'group':
                if val[0] not in group:
                    group[val[0]] = [report]
                else:
                    group[val[0]].append(report)
    return group

def reports_to_dict(myreport):
    """ Convert report.reports, report.results and report.passed to dictionary"""
    repdict = {"reports" : {}, "results": {}, "passed": False}
    for key,val in myreport.reports:
        repdict['reports'][key] = val
    for key,val in myreport.results:
        repdict['results'][key] = val
    repdict['passed'] = myreport.passed[0]

    return repdict

def is_passed(myreport):
    return myreport.passed[0]

def generate_reports_content(myreport):
    myreport = reports_to_dict(myreport)

    def conf_list_report(reports):
        listed_conf = ''
        conf_l = ["group","url","method","expected_status"]
        for key,items in reports['reports'].items():
            if key.lower() in conf_l:
                data = ''
                for item in items:
                    data+= str(item) + ", "
                data=data.rstrip(", ")
                if key == 'url':
                    key = key.upper()
                listed_conf += "<li><b>{}</b> : {} </li>".format(case_conversion(key),data)
        result = "<ul>{}</ul>".format(listed_conf)
        return result
    x=conf_list_report(myreport)
    return x

def generate_request_details(myreport):
    pp = pprint.PrettyPrinter(indent=4)
    myreport = reports_to_dict(myreport)
    ex_validators = True
    ex_body = True
    ex_headers = True
    headers = dict()
    report_res = dict()

    if 'headers' in myreport['reports'] and myreport['reports']['headers'][0]:
        for key,value in myreport['reports']['headers']:
            headers[key] = value
    else:
        ex_headers = False

    req_valid = ''
    if 'validators' in myreport['reports'] and myreport['reports']['validators']:
        for valid in myreport['reports']['validators']:
            req_valid += str(valid) + '\n'
    else:
        ex_validators = False
    req_head = pp.pformat(headers)
    if 'body' in myreport['reports']:
        req_body = pp.pformat(myreport['reports']['body'][0])
    else :
        ex_body = False

    if 'failures' in myreport['results']:
        fails = ''
        for i in myreport['results']['failures']:
            fails += "Type : {} , Message : {} </br>".format(i.failure_type, i.message)
        presfail = "<li><b>Failure :</b></br>{}</li>".format(fails)
        report_res["res_fail"] = presfail
    if ex_headers:
        req_head = convert_new_line_to_br(req_head)
        preqhead = "<li><b>Headers :</b><pre><code>{}</code></pre></li>".format(req_head)
        report_res["req_head"] = preqhead
    if ex_body:
        req_body = convert_new_line_to_br(req_body)
        preqbod = "<li><b>Body :</b><pre><code>{}</code></pre></li>".format(req_body)
        report_res["req_body"] = preqbod

    if ex_validators:
        req_valid = convert_new_line_to_br(req_valid.rstrip('\n'))
        preqval = "<li><b>Validators :</b><pre><code>{}</code></pre></li>".format(req_valid)
        report_res["req_val"] = preqval

    headers = dict()
    for key,value in myreport['results']['response_headers']:
        headers[key] = value
    res_head = pp.pformat(headers)
    res_head = convert_new_line_to_br(res_head)
    res_body = convert_new_line_to_br(myreport['results']['body'][0])
    status_code = myreport['results']['response_code'][0]

    
    preshead = "<li><b>Headers :</b><pre><code>{}</code></pre></li>".format(res_head)
    presbod = "<li><b>Body :<pre></b><code>{}</code></pre></li>".format(res_body)
    presstat = "<li><b>Status Code : </b>{}</li>".format(status_code)

    report_res["res_code"] = presstat
    report_res["res_head"] = preshead
    report_res["res_bod"] = presbod


    return report_res

def generate_title(report):
    found = False
    badge = '<span class="badge badge-danger">Failed</span>'
    card = 'bg-danger failed'
    for key,val in report.reports:
        if key=='test_name':
            nm_test = val[0]
            found = True
            break
    if not found:
        nm_test = "Noname"
    if report.passed[0] :
        card = 'success'
        badge = '<span class="badge badge-success">Passed</span>'

    t_sect = """
<div class="card {} col-12" id="{}">
<span class="card-body">
    <h5 class="card-title" >{}  {}
    </h5>""".format(card,nm_test,nm_test,badge)
    return t_sect

            
def collect_details(data_dict):
    request = dict()
    response = dict()
    for key,txt in data_dict.items():
        key = key.split("_")
        tmp = case_conversion(key[1])
        if key[0].lower() == 'req':
            request[tmp] = txt
        elif key[0].lower() == 'res':
            response[key[1]] = txt
    req_html = ''
    res_html = ''

    for key,txt in request.items():
        req_html += txt
    req_html = '<h5 class="card-title">Request</h5><ul>{}</ul>'.format(req_html)

    for key,txt in response.items():
        res_html += txt
    res_html = '<h5 class="card-title">Response</h5><ul>{}</ul>'.format(res_html)

    html_txt = req_html + res_html
    return html_txt


def generate_html_test(reports,f_name,failure=None):

    print(vars(reports[0]))
    reportgroup = dict()
    reports = cleanup(reports,f_name)
    failure = cleanup(failure,f_name)
    if failure:
        globals()['failure_report'].append((f_name,failure))
    reportgroup = group_assign(reports)
    htmltest = ''
    summary = generate_report_config(reports)
    generate_index(reports,f_name)

    for group,report in reportgroup.items():
        htmlgroup = '<div class="col-md-10 offset-md-1">'
        tmp = '<h4 style="padding-top: 15px; padding-bottom: 15px">Group : {}</h4><hr><div class="row">'.format(group)
        conf = ''
        for i in report:
            title = generate_title(i)
            conf_tmp = generate_reports_content(i)
            details = generate_request_details(i)
            details_html = collect_details(details)
            conf+= title+conf_tmp + details_html +"</span></div>"
        htmltest += htmlgroup + tmp + conf + "</div></div>"
    
    f_nav = f_name.split('/')[-1]
    success = 0
    for i in reports:
        if i.passed[0]:
            success += 1
    percent = (success/len(reports))*100
    f_nav = f_nav + ": {}%".format(round(percent))
    nav = HTMLElements(f_nav)
    nav = nav.nav()
    
    txttst = """
<html>
    <head>
    <link rel="stylesheet" href="bootstrap.css">
    <link rel="stylesheet" href="main.css">
    <link rel="stylesheet" href="datatables.css">
    </head>
    <body>{}
    <div class="container"  style="padding-top:50px;">
    <div class="row">
    {}{}
    </div></div></body>
    <script src="jquery-3.3.1.js"></script>
    <script src="main.js"></script>
    <script src="datatables.js"></script>
</html>""".format(nav,summary,htmltest)
    f_name = os.path.join(os.getcwd(),f_name)
    generate_file(f_name,txttst)

def collect_source(dest):

    from shutil import copyfile

    dirname = os.path.dirname(__file__)
    static = "../static"
    static = get_path(dirname,static)
    files = os.listdir(static)

    for f in files:
        path = "../static/{}".format(f)
        path = get_path(dirname,path)
        try:
            des = os.path.join(dest,f)
            copyfile(path,des)
        except Exception as e:
            print(str(e))
            return False
    return True

def cleanup(reports,f_name):
    results = list()
    f_name = f_name.split('/')[-1]
    f_name = f_name.split('.')[0]
    for i in reports:
        for key,val in i.reports:
            if key.lower() == 'testsets':
                testsets = val[0].split('.')
                testsets = testsets[0]
                break
        if testsets == f_name:
            results.append(i)
    return results

def generate_index(reports,f_name):
    index = os.path.join(os.path.dirname(f_name),'index.html')
    index = os.path.join(os.getcwd(),index)

    failure = globals()['failure_report']
    if failure:
        fail_txt = failure_summary(globals()['failure_report'])
    else :
        fail_txt =''

    if f_name not in globals()['test_files']:
        check = 0
        for i in reports:
            if i.passed[0]:
                check+=1
        suc_rate = "{}/{}".format(check,len(reports))
        globals()['test_files'].append((f_name,suc_rate))
    summary = globals()['test_files']
    
    def get_details(summary):
        trow = ''
        total_fail = 0
        total_success = 0
        for f,sr in summary:
            tclass = ""
            p,t = int(sr.split('/')[0]),int(sr.split('/')[1])
            total_success += p
            total_fail += (t-p)
            percent = round((p/t)*100)
            if percent < 100:
                tclass = 'table-danger'
            trow += '<tr class = "{}">'.format(tclass)
            path = get_path(os.getcwd(),f)
            td = '<td><a href={}>{}</a></td>'.format(f.split('/')[-1],path)
            td+= '<td>{}</td>'.format(sr)
            td+= '<td>{}%</td>'.format(percent)
            trow += '{}</tr>'.format(td)
        total_result = "{}/{}".format(total_success,(total_fail+total_success))
        percent = total_success*100/(total_fail+total_success)
        table = """
        <div class="container" style="padding-top:50px;">
        <div class="row">
        <div class="col-md-10 ">
        <table id="sumTable" class="table table-sm table-bordered table-list-search">
            <thead>
                <tr>
                    <th>Test Files</th>
                    <th>Result (Success/Tests)</th>
                    <th>Success rate (%)</th>
                </tr>
            </thead>
            <tbody>
            {}
            </tbody>
            <tfoot>
            <tr class="table-info"><td style="text-align:center;">
            <b>Total Result</b></td>
            <td>{}</td>
            <td>{}%</td></tr></tfoot>
        </table></div>""".format(trow,total_result,round(percent))
        return table,percent
    table_content,percent=get_details(summary)
    elements = HTMLElements('index {}'.format(round(percent)))
    nav = elements.nav()
    txttst = """
<html>
    <head>
    <link rel="stylesheet" href="bootstrap.css">
    <link rel="stylesheet" href="main.css">
    <link rel="stylesheet" href="datatables.css">
    </head>
    <body>
    {}
    {}
    </div>
        <div class="row">{}
        </div>
    </div>

    </body>
    <script src="jquery-3.3.1.js"></script>
    <script src="main.js"></script>
    <script src="datatables.js"></script>
</html>""".format(nav,table_content,fail_txt)

    generate_file(index,txttst)



class HTMLElements():

    is_index = False
    is_report = False
    head_title = ''
    
    def __init__(self,page):
        if "index" in page.lower():
            self.is_index = True
            self.is_report = False
            page = page.split(" ")
            pct = page[-1]
            self.head_title = "General Summary : {}%".format(pct)
        else:
            self.is_report = True
            self.is_index = False
            self.head_title = page

    def nav(self):
        search_bar = """<form>
  <button id="filterSuc" class="button btn-success btn-small buttons-right">Hide Success</button>
  <button id="filterFail" class="button btn-danger btn-small buttons-right">Hide Fail</button>
    </form>
"""
        indexlink = '<a href="index.html" class="navbar-brand right" style="color:black;">Back to Index</a>'

        if self.is_index:
            attach = search_bar
        else:
            attach = indexlink + search_bar
        navhtml = """
<nav class="navbar navbar-dark bg-light justify-content-between">
  <a class="navbar-brand" >{}</a>
  {}
</nav>""".format(self.head_title,attach)
        return navhtml


def generate_benchmark_title(benchmark_report):
    
    bench_name = benchmark_report.config['name']
    
    card_head = """
    <div class="card col-12" id="{}">
    <span class="card-body">
    <h5 class="card-title" >{} 
    </h5>
    """.format(bench_name,bench_name)

    return card_head

def construct_benchmark_card(benchmark_report):

    html_text = ""
    for report in benchmark_report:
        title = generate_benchmark_title(report)
        config = benchmark_result_details(report)
        data_table = benchmark_result_table(report)
        html_text += "{}{}{}</span></div>".format(title,config,data_table)
    return html_text

def failure_summary(fail_report):
    html_out = ''
    for key,fail in fail_report:
        htmlgroup = '<div class="col-md-10">'
        tmp = '<h4 style="padding-top: 15px; padding-bottom: 15px">Test_file : {}</h4><hr><div class="row">'.format(key)
        conf = ''
        for i in fail:
            content = generate_reports_content(i)
            raw_details = generate_request_details(i)
            title = generate_title(i)
            details = collect_details(raw_details)
            conf+= title + content + details + "</span></div>"
        html_out += htmlgroup + tmp + conf + "</div></div>"

    return html_out

def benchmark_result_details(benchmark_report):
    html_out = ""
    config = {**benchmark_report.config, **benchmark_report.processed_report}    
    for key,value in config.items():
        tmp = ""
        if not(isinstance(value,list) or isinstance(value,dict) or isinstance(value,tuple)):
            tmp = "{}  :  {}<br/>".format(case_conversion(key),str(value))
        else:
            tmp+= "{}  :<br/>".format(case_conversion(key))
            if isinstance(value,list) and not isinstance(value[0],tuple):
                for item in value:
                    tmp += "  {}<br/>".format(str(value))
            elif isinstance(value,dict):
                for subkey,subval in value.items():
                    tmp += "  {}  :  {}<br/>".format(case_conversion(subkey),str(subval))
            elif isinstance(value,list) and isinstance(value[0],tuple):
                for subkey,subval in value:
                    tmp += "  {}  :  {}<br/>".format(case_conversion(subkey),str(subval))
        html_out+=tmp
    html_out = "<pre><code>{}</code></pre>".format(html_out)
    return html_out



def benchmark_result_table(benchmark_report):
    html_out = ""
    table_head = ""
    table_data = ""
    result = benchmark_report.result_item

    list_data = list()
    header = list()
    for item in range(0,len(result)):
        header.append(result[item][0])
        list_data+=result[item][1]    
    index = len(result[0][1])    
    data = list()
    for item in range(0,index):
        tmp = list()
        for x in range(0,len(result)):
            idx = item + (index*x)
            tmp.append(list_data[idx])
        tmp = tuple(tmp)
        data.append(tmp)
    for key,value in result:
        table_head += "<th>{}</th>".format(case_conversion(key))
    for row in data:
        tmp = ""
        for item in row:
            tmp += "<td>{}</td>".format(str(item))
        table_data += "<tr>{}</tr>".format(tmp)
   
    table_head = "<thead>{}</thead>".format(table_head)
    table_data = "<tbody>{}</tbody>".format(table_data)
    html_out = '<table class="table">{}{}</table>'.format(table_head,table_data)
    return html_out


class BenchmarkReport(object):
    benchmark_results = None
    results_item = list()   
    processed_report = dict()
    config = dict()

    def __init__(self,result=None):
        self.benchmark_results = result
        try:
            result_list = result['results']
            self.result_item = list(result_list.items())   
        except:
            pass

        try:
            processed = result['aggregates']
            temp = dict()
            for item in processed:
                if item[0] in temp:
                    temp[item[0]].append((item[1],item[2]))    
                else:
                    temp[item[0]] = list()
                    temp[item[0]].append((item[1],item[2]))
            self.processed_report = temp
        except:
            pass

        temp = copy(result)
        temp.pop('aggregates',None)
        temp.pop('results',None)
        self.config = temp


def generate_benchmark_report(benchmark_report,f_name):
    
    report_cards = construct_benchmark_card(benchmark_report)
    
    txttst = """
<html>
    <head>
    <link rel="stylesheet" href="bootstrap.css">
    <link rel="stylesheet" href="main.css">
    <link rel="stylesheet" href="datatables.css">
    </head>
    <body>
    </div>
        <div class="row">
            <div class="container"  style="padding-top:50px;">
                <div class="row">
                {}
                </div>
            </div>
        </div>
    </div>

    </body>
    <script src="jquery-3.3.1.js"></script>
    <script src="main.js"></script>
    <script src="datatables.js"></script>
</html>""".format(report_cards)

    f_name = os.path.join(os.getcwd(),f_name)
    generate_file(f_name,txttst)

class BenchmarkData(object):

    data = None
    url = None
    dataset_name = "NoName"
    is_dictionary = False

    def write_data(self,data,is_processed_data=False):
        temp_headers = list()
        temp_data = dict()
        if isinstance(data,tuple):
            if len(data) != 2:
                raise TypeError("Tuple's lenght must be 2! {}".format(data))
            else:
                if isinstance(data[1],list):
                    temp_headers.append(data[0])
                    temp_data[data[0]] = data[1]
                elif isinstance(data[1],str) or isinstance(data[1],int) or isinstance(data[1],float):
                    temp_headers.append(data[0])
                    temp_data[data[0]] = [data[1]]
                elif isinstance(data[1],tuple) or isinstance(data[1],dict):
                    self.write_data(data[1],is_processed_data=is_processed_data)
        elif isinstance(data,dict):
            for key,value in data.items():
                self.is_dictionary = True
                temp_headers.append(key)
                temp_data[key] = value
        else:
            raise TypeError("Data must be tuple or dictionary ! : {}".format(data))
        
        if is_processed_data :
            self.processed_data = temp_data
            self.processed_headers = temp_headers
        else:
            self.raw_data = temp_data
            self.raw_headers = temp_headers


class HTMLObject(object):
    single_tag = False
    tag = ''
    attribute = dict()
    content = ""
    _label = ""

    def __init__(self,obj,**kwargs):
        for key,value in obj.items():
            self.__setattr__(key,value)
        if kwargs:
            self.__setattr__(key,value)
        self.configure_klass()

    
    def configure_klass(self):
        klass = self.attribute.get('klass',None)
        if klass:
            klass_list = [key for key,value in klass.items() if value]
            klass_str = ""
            for item in klass_list:
                klass_str+= item + " "
            self.attribute['klass'] = klass_str
            return klass_str
        else:
            return ""

    def build(self):
        if isinstance(self.content,HTMLObject):
            self.content = self.content.build()
            return self.build()
        elif isinstance(self.content,list):
            content_tmp = ""
            for item in self.content:
                if not isinstance(item,HTMLObject):
                    raise TypeError("HTMLObject.content must be a string, an HTMLObject or a list of HTMLObject : {} : {}".format(item,type(item)))
                content_tmp += item.build()
            self.content = content_tmp
            return self.build()
        else:
            attr = self.attribute
            doc,tag,text = Doc().tagtext()
            with tag(self.tag,**attr):
                doc.asis(self.content)
            return doc.getvalue()



class DataTable(object):
    
    raw_datasets = dict()
    raw_data = dict()
    raw_head = list()
    html_attr = dict()
    head = list()
    data_length = None
    data = None

    DEFAULT_ATTRIBUTE = {
        "table" : {
            "klass" : {"table" : True, "table-sm" : True, "table-bordered" : True, "table-list-search" : True},
            "id" : "sumTable"

        }
    }

    def __init__(self,raw_data):
        try:
            self.raw_datasets = copy(raw_data)
            self.raw_head = list(raw_data.keys())
            self.head = [case_conversion(x) for x in self.raw_head]        
            for key,value in self.raw_datasets.items():
                data = [x['value'] for x in value]
                attr = [x.get('attribute',{}) for x in value]
                self.html_attr[key] = attr
                self.raw_data[key] = data
                self.data_length = len(self.html_attr[self.raw_head[0]])

        except Exception as e:
            raise Exception(str(e))
        

    def prepare_html_attr(self):
        attr = list()
        for idx in range(0,self.data_length):
            tmp = {}
            for key in self.raw_head:
                tmp = {**tmp,**self.html_attr[key][idx]}
            attr.append(tmp)
        return attr

    def prepare_cell_data(self):
        data = list()
        for idx in range(0,self.data_length):
            tmp = []
            for key in self.raw_head:
                tmp.append(self.raw_data[key][idx])
            data.append(tmp)
        return data

    def construct_hmtl_dict(self,tag,content,attr={}):
        result = {
            "tag" : tag,
            "attribute" : attr,
            "content" : content
        }
        return result

    def combine_attr(self,attr):
        tmp = dict()
        klass = attr.get('klass',{})
        klass = {**self.DEFAULT_ATTRIBUTE['klass'],**klass}
        tmp = {**attr, **self.DEFAULT_ATTRIBUTE}
        tmp['klass'] = klass
        return tmp


    def construct_table_object(self):
        cell_data = self.prepare_cell_data()
        attr = self.prepare_html_attr()
        head = self.raw_head
        head_title = self.head


        tmp = [self.construct_hmtl_dict('td',x) for x in head_title]
        o_head = [HTMLObject(item) for item in tmp]
        o_head_row = HTMLObject(self.construct_hmtl_dict('tr',o_head))
        o_thead = HTMLObject(self.construct_hmtl_dict('thead',o_head_row))
        
        o_tr_data = []
        for data,_attr in zip(cell_data,attr):
            tmp = [HTMLObject(self.construct_hmtl_dict('td',x)) for x in data]
            o_tr_data.append(HTMLObject(self.construct_hmtl_dict('tr',tmp,_attr)))
        o_tbody = HTMLObject(self.construct_hmtl_dict('tbody',o_tr_data))

        tmp = [o_thead,o_tbody]
        o_table = HTMLObject(self.construct_hmtl_dict('table',tmp,self.DEFAULT_ATTRIBUTE['table']))
        
        return o_table





class DataChart(BenchmarkData):

    chart_type = "scatter"
    chart_data = None
    chart_name = "NoName"


    canvas_elements = dict()
    plot_configuration = dict()
    DEFAULT_DATASETS_CONFIG = { "scatter" : {"borderWidth" : 1 , "pointRadius":5 , "pointHoverRadius" : 7}
                                }
    DEFAULT_OPTIONS = {"scatter" : { "scales" : { "yAxes": [{"ticks" : { "beginAtZero" : True}}], "xAxes" : [{"ticks" : {"stepSize" : 1}}]}},
                       "bar" : {"scales":{"xAxes":[{"barPercentage":0.5,"barThickness":6,"maxBarThickness":8,"minBarLength":2,"gridLines":{"offsetGridLines":True}}]}}}

    def __init__(self,obj_data, **kwargs):
        if kwargs:
            for key,value in kwargs.items():
                if key == ['chart_type']:
                    self.chart_type = value
        self.obj_data = obj_data
        plotdata = self.get_data(obj_data,self.chart_type)
        plotdata = self.dataset_checking(self.chart_type,plotdata)
        self.chart_data = plotdata
        if kwargs:
            self.plot_configuration = self.construct_configuration(**kwargs)

    def construct_script(self):
        conf = copy(self.plot_configuration)
        mychart = self.chart_name
        doc,tag,text = Doc().tagtext()
        with tag('script'):
            script ="var ctx = document.getElementById('{}').getContext('2d');var {} = new Chart(ctx,{})".format(mychart,mychart,conf)
            text(script)
        return doc

    def get_script(self):
        script = self.construct_script()
        return script.getvalue()

    def construct_configuration(self,**kwargs):
        chart_type = self.chart_type
        tmp = dict()
        if kwargs:
            for key,value in kwargs.items():
                if key == 'labels':
                    if isinstance(value,list):
                        labels = value
                    elif isinstance(value,str):
                        labels = [value]
                    else:
                        raise ValueError("Invalid type, must be list or str : {}".format(value))
                elif key == 'bordercolor':
                    if isinstance(value,list):
                        tmp['borderColor'] = value
                    elif isinstance(value,str):
                        tmp['borderColor'] = [value for x in range(0,len(self.chart_data))]
                    else:
                        raise ValueError("Invalid type, must be list or str : {}".format(value))
                elif key == 'pointbackgroundcolor':
                    if isinstance(value,list):
                        tmp['pointBackgroundColor'] = value
                    elif isinstance(value,str):
                        tmp['pointBackgroundColor'] = [value for x in range(0,len(self.chart_data))]
                    else:
                        raise ValueError("Invalid type, must be list or str : {}".format(value))        
        else:
            labels = [index+1 for index in range(0,len(self.chart_data))]
        
        tmp['data'] = self.chart_data
        tmp['label'] = self.chart_name
        tmp = {**self.DEFAULT_DATASETS_CONFIG[chart_type],**tmp}
        options = copy(self.DEFAULT_OPTIONS[chart_type])
        
        configurated_chart = {"type":chart_type,"data" : { "labels" : labels, "datasets":[tmp]},"options":options}
        return configurated_chart


    def plot_graph(self):
        pass

    
    def get_html(self):
        html = self.construct_canvas_elements()
        return html.getvalue()
    
    
    def construct_canvas_elements(self):
        attr = copy(self.canvas_elements)
        
        doc,tag,text = Doc().tagtext()

        with tag("canvas",**attr):
            with tag("p"):
                text("Your browser does not support the canvas element.")
        
        return doc
    
    def parse_canvas_element(self):
        self.canvas_elements['id'] = self.chart_name
        self.canvas_elements['role'] = 'img'



    def configure_chart(self,key,value):
        return self.__setattr__(key,value)

    def get_data(self,obj_data,chart_type):
        chartdata = list()
        if chart_type == 'scatter':
            for key,value in obj_data.items():
                self.configure_chart("chart_name",key)
                for item in range(0,len(value)):
                    tmp = {"x" : item+1, "y" : value[item]}
                    chartdata.append(tmp)
        elif chart_type == 'bar':
            for key,value in obj_data.items():
                self.configure_chart("chart_name",key)
                chartdata = value
        self.chart_data = chartdata
        return chartdata

    def dataset_checking(self,charttype,chartdata):
        msg = ""
        is_wrong = False
        if charttype == 'scatter':
            if isinstance(chartdata,list):
                for item in chartdata:
                    if not isinstance(item,dict):
                        is_wrong = True
                        temp = item
            else:
                is_wrong = True
                temp = chartdata
            if is_wrong:
                msg = "Scatter Chart must have list(dict()) as data type : {}".format(temp)
        elif charttype == 'bar':
            if isinstance(chartdata,list):
                for item in chartdata:
                    if not isinstance(item,dict) or not isinstance(item,int) or not isinstance(item,float):
                        is_wrong = True
                        temp = item
            else:
                is_wrong = True
                temp = chartdata
            if is_wrong:
                msg = "Bar Chart must have list(dict()) as data type : {}".format(temp)
        if charttype == 'line':
            if isinstance(chartdata,list):
                for item in chartdata:
                    if not isinstance(item,dict):
                        is_wrong = True
                        temp = item
            else:
                is_wrong = True
                temp = chartdata
            if is_wrong:
                msg = "Line Chart must have list(dict()) as data type : {}".format(temp)
        if is_wrong:
            raise ValueError(msg)
        else:
            return chartdata