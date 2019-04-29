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

def generate_summary(myreport):
    keys = {"test_name","group","method","url","status"}
    table_data = dict()
    table_data.fromkeys(keys,[])
    for key in keys:
        table_data[key] = list()
        for report in myreport:
            temp = {**report.raw_details, **report.identity}
            attr = {"klass" : {"table-danger" : report.is_failed , "clickable-row" : True}, "data-url" : "#{}".format(report.identity['test_name'])}
            value = temp.get(key)
            tmp = {"value" : value , "attribute" : attr}
            table_data[key].append(tmp)
    table_out = DataTable(table_data)
    table_out=table_out.construct_table_object()
    div_out = construct_html_dict('div',table_out,{'klass': {'col-md-10' : True, 'offset-1':True}})
    div_out = HTMLObject(div_out)
    return div_out



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
    
    myreport = list()
    rep_success = 0
    for report in reports:
        tmp = {"results" : report.results, "reports" : report.reports , "passed" : report.passed}
        x = DataReport(tmp)
        myreport.append(x)
        if report.passed[0]:
            rep_success += 1
    
    percentage = (rep_success/len(reports))*100
    percentage = round(percentage,2)
  
    grouping(myreport)
    reportgroup = dict()
    reports = cleanup(reports,f_name)
    failure = cleanup(failure,f_name)
    if failure:
        globals()['failure_report'].append((f_name,failure))
    reportgroup = group_assign(reports)
    htmltest = ''
    summary=[generate_summary(myreport)]
    html_report = grouping(myreport)
    generate_index(reports,f_name)

    f_nav = f_name.split('/')[-1]
    f_nav = f_nav + ": {}%".format(percentage)
    nav = HTMLElements(f_nav)
    nav = nav.nav()

    stylesheet,script = generate_source()
    head = construct_html_object("head",stylesheet)
    row_content = summary + html_report
    row = construct_html_object("div",row_content,{"klass" : {"row" : True}})
    container = construct_html_object("div",row,{"klass" : {"container" : True}, "style" : "padding-top : 50px;"})

    body_content = [nav,container]
    body = construct_html_object("body",body_content)
    html_content = [head,body]+script
    html = construct_html_object("html",html_content)
    txttst = html.build()
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


def grouping(myreports):

    grouped_report = dict()
    for report in myreports:
        group_name = report.identity['group']
        if group_name not in grouped_report:
            grouped_report[group_name] = list()
        grouped_report[group_name].append(report.construct())
    
    style = "padding-top: 15px; padding-bottom: 15px"
    obj_group = list()
    for group,reports in grouped_report.items():
        tmp = "Group : {}".format(case_conversion(group))
        group_title = construct_html_dict('h4', tmp, {"style":style})
        group_title = HTMLObject(group_title)
        l_break = HTMLObject(construct_html_dict('hr',''))
        row = HTMLObject(construct_html_dict('div',reports,{'klass' : {'row' : True}}))
        group_section = construct_html_dict('div',[group_title,l_break,row],{'klass' : {'col-md-10' : True,  'offset-md-1' : True}})
        x = HTMLObject(group_section)
        obj_group.append(x)        
    
    return obj_group

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
        attr = {"href" : "index.html" , "style" : "color:black", "klass" : {"navbar-brand" : True, "right" : True}}
        indexlink = construct_html_dict('a',"Back to Index",attr=attr)
        indexlink = HTMLObject(indexlink)

        buttonSuc = construct_html_dict("button","Hide Succes",{"id" : "filterSuc", "klass": {"button" : True, "btn-success" : True, "btn-small": True, "buttons-right":True}})
        buttonFail = construct_html_dict("button","Hide Fail",{"id" : "filterFail", "klass": {"button" : True, "btn-danger" : True, "btn-small": True, "buttons-right":True}})
        search_bar = construct_html_dict("form",[HTMLObject(buttonSuc),HTMLObject(buttonFail)])
        search_bar = HTMLObject(search_bar)

        
        title = construct_html_dict("a",self.head_title,{"klass" : {"navbar-brand" : True}})
        title = HTMLObject(title)

        if self.is_index:
            attach = [title,search_bar]
        else:
            attach = [title,indexlink,search_bar]

        navhtml = construct_html_dict("nav",attach,{"klass" : {"navbar" : True, "navbar-dark" : True, "bg-light" : True, "justify-content-between":True}})

        return HTMLObject(navhtml)


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
        self.attribute = dict()
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
                if isinstance(item,HTMLObject):
                    content_tmp += item.build()
                elif not item:
                    continue
                else:
                    content_tmp += str(item)
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
        self.raw_datasets = dict()
        self.raw_data = dict()
        self.raw_head = list()
        self.html_attr = dict()
        self.head = list()
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


        tmp = [construct_html_dict('th',x) for x in head_title]
        o_head = [HTMLObject(item) for item in tmp]
        o_head_row = HTMLObject(construct_html_dict('tr',o_head))
        o_thead = HTMLObject(construct_html_dict('thead',o_head_row))
        
        o_tr_data = []
        for data,_attr in zip(cell_data,attr):
            tmp = [HTMLObject(construct_html_dict('td',x)) for x in data]
            o_tr_data.append(HTMLObject(construct_html_dict('tr',tmp,_attr)))
        o_tbody = HTMLObject(construct_html_dict('tbody',o_tr_data))

        tmp = [o_thead,o_tbody]
        o_table = HTMLObject(construct_html_dict('table',tmp,self.DEFAULT_ATTRIBUTE['table']))
        
        return o_table

class DataReport(object):

    is_failed = False

    
    reportObject = None    


    def __init__(self,data,**kwargs):
        self.raw_details = dict()
        self.raw_request = dict()
        self.raw_response = dict()
        self.identity = dict()
        self.parse_reports(data)

    def parse_reports(self,data):
        result = tuples_to_dict(data['results'])
        report = tuples_to_dict(data['reports'])
        self.is_failed = not(data.pop('passed')[0])

        self.identity['test_sets'] = report.pop("testsets")[0]
        self.identity['test_name'] = report.pop("test_name")[0]
        self.identity['group'] = report.pop("group")[0]
        if self.is_failed:
            self.identity['status'] = 'Failed'
        else:
            self.identity['status'] = 'Passed'

        if self.is_failed:
            failure = result.pop('failures')
            failure = failure[0]
            txt = "Type : {} , Message : {}".format(failure.failure_type,failure.message)
            self.raw_details['failures'] = [txt]

        self.raw_details['method'] = report.pop('method')
        self.raw_details['url'] = report.pop('url')
        self.raw_details['expected_status'] = report.pop('expected_status')

        self.raw_request = copy(report)

        self.raw_response = copy(result)

        self.raw_request['validators'] = report.get('validators',{})
        try:
            report.pop('validators')
        except:
            pass

    def generate_list(self,d_list):
        list_item = list()
        for key,value in d_list.items():
            content = ""
            if isinstance(value,list):
                for val in value:
                    content+=str(val) + ", "
                content = content.rstrip(", ")
            else:
                content = value
            bullet = construct_html_dict('b',"{} :  ".format(case_conversion(key)))
            o_list = construct_html_dict('li',[HTMLObject(bullet),content])
            o_list = HTMLObject(o_list)
            list_item.append(o_list)
        result = construct_html_dict('ul',list_item)
        return HTMLObject(result)


    def generate_code(self,data):
        
        data = convert_new_line_to_br(data)
        obj = construct_html_dict('code',data)
        obj = HTMLObject(obj)

        o_pre = construct_html_dict('pre',obj)
        o_pre = HTMLObject(o_pre)
        return o_pre

    def construct(self):
        
        card_title = self.identity.get('test_name','Untitled')
        card_badge = generate_badge(not(self.is_failed))
        card_title = construct_html_dict('h5',[(card_title+"    "),card_badge],{'klass' : {'card-title':True}})
        card_title = HTMLObject(card_title)

        card_details = self.generate_list(self.raw_details)
        card_request = None
        request_title = None
        if self.raw_request:
            card_request = list()
            request_title = construct_html_dict('h5','Request',{'klass' : {'card-title' : True}})
            request_title = HTMLObject(request_title)
            for key,value in self.raw_request.items():
                if isinstance(value,list):
                    value = value[0]
                if isinstance(value,dict):
                    value = json.dumps(value)
                elif not value:
                    continue   
                value = convert_new_line_to_br(value)
                o_code = self.generate_code(value)
                key_title = case_conversion(key)
                key_title = construct_html_dict('b',case_conversion(key_title))
                key_title = HTMLObject(key_title)
                o_li = construct_html_dict('li',[key_title,o_code])
                card_request.append(HTMLObject(o_li))
            card_request = construct_html_dict('ul',card_request)
            card_request = HTMLObject(card_request)

        card_response = list()
        response_title = construct_html_dict('h5','Response',{'klass' : {'card-title' : True}})
        response_title = HTMLObject(response_title)
        pp = pprint.PrettyPrinter(indent=4)
        for key,value in self.raw_response.items():
            tmp = key
            key = construct_html_dict('b',"{} :".format(case_conversion(key)))
            key = HTMLObject(key)
            if tmp.lower() == 'response_headers':
                value = pp.pformat(value)
            if isinstance(value,list):
                value = value[0]
            elif isinstance(value,dict):
                value = json.dumps(value)
            elif not value:
                continue
            value = self.generate_code(value)
            li = construct_html_dict('li',[key,value])
            li = HTMLObject(li)
            card_response.append(li)
        card_response = construct_html_dict('ul',card_response)
        card_response = HTMLObject(card_response)

        content_span = [card_title,card_details,request_title,card_request,response_title,card_response]

        o_span = construct_html_dict('span',content_span,{'klass':{'card-body':True}})
        o_span = HTMLObject(o_span)

        klass = {"id" : self.identity['test_name'], "klass" : {"card" : True,"success" : not(self.is_failed) ,"bg-danger":self.is_failed, "failed" : self.is_failed, "col-12":True}}

        o_div = construct_html_dict('div',o_span,klass)
        return HTMLObject(o_div)

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
        content = "var ctx = document.getElementById('{}').getContext('2d');var {} = new Chart(ctx,{})".format(mychart,mychart,conf)
        script = construct_html_dict("script",content)
        script = HTMLObject(script)
        return script

    def get_script(self):
        script = self.construct_script()
        return script.build()

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
        attr = copy(self.canvas_elements)
        default = construct_html_dict("p","Your browser does not support the canvas element.")
        default = HTMLObject(default)

        canvas = construct_html_dict("canvas",default,attr=attr)
        canvas = HTMLObject(canvas)


        return canvas


    
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


def construct_html_dict(tag,content,attr={}):
    result = {
        "tag" : tag,
        "attribute" : attr,
        "content" : content
    }
    return result

def construct_html_object(tag,content,attr={}):
    return HTMLObject(construct_html_dict(tag,content,attr))


def generate_badge(value):
    txt = "Failed"
    attr = dict()
    klass = {"badge" : True, "badge-success": False, "badge-danger":True}
    if value:
        txt = "Passed"
        klass['badge-success'] = True
        klass['badge-danger'] = False
    attr['klass'] = klass
    attr['style'] = "margin-left : 15px;"
    html_dict = {"tag" : "span", "content": txt, "attribute":attr}
    return HTMLObject(html_dict)

def check_list_of_tuples(data):
    for i in data:
        if not isinstance(i,tuple) or not len(i) is 2:
            raise TypeError("Value must be list of tuples of 2 elements : {}".format(i))
    return True 



def tuples_to_dict(tuples):
    result = dict()
    for key,value in tuples:
        if isinstance(value,list) and isinstance(value[0],tuple) and check_list_of_tuples(value):
            value = tuples_to_dict(value)
        result[key] = value
    return result



def generate_source():

    dirname = os.path.dirname(__file__)
    static = "../static"
    static = get_path(dirname,static)
    files = os.listdir(static)

    stylesheet = list()
    script = list()


    for item in files:
        f_type = item.split('.')[-1]
        if f_type == 'css':
            tmp = construct_html_dict('link',"",{"rel" : "stylesheet", "href" : item})
            tmp = HTMLObject(tmp)
            stylesheet.append(tmp)
        else:
            tmp = construct_html_dict('script',"",{"src" : item})
            tmp = HTMLObject(tmp)
            script.append(tmp)
    
    return stylesheet,script