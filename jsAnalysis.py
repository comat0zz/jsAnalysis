#!/usr/bin/env python3.6
# -*- coding: utf-8 -*- 

import re
import argparse
import os
import html
from datetime import datetime
import codecs
from bs4 import BeautifulSoup

with_brackets = [
    # Write raw HTML
    'document.write',
    'document.writeln',
    # Directly modifying the DOM (including DHTML events)
    'document.attachEvent',
    'document.execCommand',
    'window.attachEvent',
    # Replacing the document URL
    'document.location.replace',
    'document.location.assign',
    'window.navigate',
    # Opening/modifying a window
    'document.open',
    'window.open',
    # Directly executing script
    'eval',
    'window.execScript',
    'window.setInterval',
    'window.setTimeout',
    # Requests
    'xmlhttp.open',
    'ActiveXObject'
]

with_brackets = '|'.join(with_brackets)
with_brackets = with_brackets.replace('.', '\.')
with_brackets = r'(%s)\s?\(' % with_brackets
pattern_brackets = re.compile(with_brackets)

with_equally = [
    # Write raw HTML
    '.innerHtml',
    '.outerHTML',
    # Replacing the document URL
    'document.location',
    'document.location.hostname',
    'document.URL',
    # Opening/modifying a window
    'window.location.href'
]

with_equally = '|'.join(with_equally)
with_equally = with_equally.replace('.', '\.')
with_equally = r'(%s)\s?\=' % with_equally
pattern_equally = re.compile(with_equally)

# Various other collections
pattern_forms = re.compile(r'(document\.forms\[[0-9]+\]\.action\s?)')

# Requests
pattern_http = re.compile(r'XMLHttpRequest\s?')

# Javascript
pattern_js = re.compile(r'javascript\:\s?')


def run(project):
    '''Функция не сразу строит отчет, чтобы можно было использовать различные врапперы'''	
    
    RESULTS = []

    # Чтобы не уезжать вправо на куче if's
    js_files = []

    for root, dirs, files in os.walk(project):
        for file in files:
            if file.endswith(".js"):
                js_files.append(os.path.join(root, file))

    for js_file in js_files:
        body = None
        with open(js_file) as f:
            body = f.readlines()
            body = [x.strip() for x in body]

        if body is None:
            continue

        result_page = []
        line_count = 0
        for line in body:

            line_count += 1
            
            if line == '':
                continue

            # На случай комментариев
            if (line[0] == '*' or line[0:1] == '/*'):
                continue

            res_brackets = re.findall(pattern_brackets, line)
            res_equally = re.findall(pattern_equally, line)
            res_forms = re.findall(pattern_forms, line)
            res_http = re.findall(pattern_http, line)
            res_js = re.findall(pattern_js, line)

            if ( res_js != [] or res_http != [] or res_forms != [] or res_equally != [] or res_brackets != [] ):
                
                result_page.append({'line': html.escape(line), 'number': line_count})


        if result_page != []:
            RESULTS.append({'results': result_page, 'fullpath': js_file})

    return RESULTS

def report(res, path):
    '''Генерация HTML отчета на основе собранных данных'''

    report_name = 'jsAnalysis_%s.html' % datetime.now()
    path_report = os.path.join(path, report_name)

    with open('template.html') as f:
        tpl = ''.join(f.readlines())

    soup = BeautifulSoup(tpl, 'html.parser')

    for ar in res:

        tr_line = '''<tr><td colspan="2">%s</td></tr>''' % ar['fullpath']
        tr_line = BeautifulSoup(tr_line, 'html.parser')
        soup.section.table.tbody.append(tr_line)
        for r in ar['results']:
            
            tr_line = '''<tr><td>%s</td><td>%s</td></tr>''' % (r['number'], r['line'])
            tr_line = BeautifulSoup(tr_line, 'html.parser')
            soup.section.table.tbody.append(tr_line)


    tpl = codecs.open(path_report, 'w', 'utf-8')
    tpl.write(str(soup))
    tpl.close()


def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', dest='project', required=True,
        help='Каталог проекта к проверке.')

    return parser

if __name__ == '__main__':
    
    parser = createParser()
    namespace = parser.parse_args()

    result = run(namespace.project)

    report(result, namespace.project)
