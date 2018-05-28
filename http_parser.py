import cgi
from urlparse import parse_qs
import re
from StringIO import StringIO

import os


class HTTPRequest:
    def __init__(self, data):
        headend = data.find("\r\n\r\n")
        rfile = ""
        if headend > 0:
            rfile = data[headend + 4:]
            headlist = data[0:headend].split("\r\n")
        else:
            headlist = data.split("\r\n")
        self.rfile = StringIO(rfile)
        first_line = headlist.pop(0)
        self.command, self.path, self.http_version = re.split('\s+', first_line)
        indexlist = self.path.split('?')
        self.baseuri = indexlist[0]
        ''.strip('/')
        parts = self.baseuri.strip('/').split('/', 2)
        if len(parts) != 2:
            raise Exception('uri path is invalid')
        self.controller, self.action = parts[:2]

        self.headers = {}
        for item in headlist:
            if item.strip() == "":
                continue
            segindex = item.find(":")
            if segindex < 0:
                continue
            key = item[0:segindex].strip()
            value = item[segindex + 1:].strip()
            self.headers[key] = value
        c_low = self.command.lower()
        self.getdic = None
        self.form = None
        self.post = None
        self.postdic = None
        self.getdic = parse_qs(self.path.split("?").pop())
        if c_low == "get" and "?" in self.path:
            pass
        elif c_low == "post" and self.headers.get('Content-Type', "").find("boundary") > 0:
            self.form = cgi.FieldStorage(fp=self.rfile, headers=None,
                                         environ={'REQUEST_METHOD': self.command,
                                                  'CONTENT_TYPE': self.headers['Content-Type'], })
            if self.form is None:
                self.form = {}
        elif c_low == "post":
            self.postdic = parse_qs(rfile)
            self.post = rfile
