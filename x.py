import urllib2
import traceback
import sys
import json

class Dingus(object):
    def error(self):
        1/0

def submit_exception(app_name):
    exc_type, exc_value, exc_traceback = sys.exc_info()
    exc_name = str(exc_type.__name__)
    lines = []
    for line in traceback.format_tb(exc_traceback):
        for sl in line.split('\n'):
            lines.append(sl.strip())
    lines = "\n".join(lines)

    url = "http://localhost:8888/add"
    data = {'name': "%s.%s" % (app_name, exc_name),
             'meta': {
                 'type': 'exception',
                 'name': exc_name,
                 'value': str(exc_value),
                 'lineno': exc_traceback.tb_lineno,
                 'lines': lines}}
    resp = urllib2.urlopen(url, json.dumps(data))
    resp.read()
    resp.close()


for i in (1,):
    try:
        Dingus().error()
    except Exception:
        submit_exception('extraction')
