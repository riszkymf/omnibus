import json
import pprint
import os
from lxml import etree
from omnibus.libs.util import *
from omnibus.libs.parsing import safe_to_json

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