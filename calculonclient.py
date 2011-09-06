import urllib2
import traceback
import sys
import json
from tornado.httpclient import AsyncHTTPClient

#class Dingus(object):
    #def error():
        #1/0

URL = "http://localhost:8888/add"

def get_exception_info():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    exc_name = str(exc_type.__name__)
    lines = []
    for line in traceback.format_tb(exc_traceback):
        for sl in line.split('\n'):
            lines.append(sl.strip())
    lines = "\n".join(lines)
    return (exc_name, exc_value, exc_traceback.tb_lineno, lines)

def generate_json_record(key_name, exc_name, exc_value, lineno, lines):

    exc_name, exc_value, lineno, lines = get_exception_info()
    data = {'name': "%s.%s" % (key_name, exc_name),
             'meta': {
                 'type': 'exception',
                 'name': exc_name,
                 'value': str(exc_value),
                 'lineno': lineno,
                 'lines': lines}}
    return data

def submit_exception(counter_name):

    url = "http://localhost:8888/add"
    data = generate_json_record(counter_name)
    resp = urllib2.urlopen(url, json.dumps(data))
    resp.read()
    resp.close()


def tcount_exception(counter_name):
    exc_name, exc_value, lineno, lines = get_exception_info()
    data = generate_json_record(counter_name, exc_name, exc_value, lineno, lines)
    # configure to use the better fetch method
    AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
    # make the actual call to the counter
    AsyncHTTPClient().fetch(URL, lambda resp: None, method="POST", body=json.dumps(data))


def tcount(counter_name):
    AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
    AsyncHTTPClient().fetch('http://localhost:8888/inc/%s' % counter_name, lambda resp: None)

