import select

import vars
from http_parser import HTTPRequest


class Worker(object):
    def __init__(self):
        pass

    def process(self, data, epoll_fd, fd):
        res = ""
        add_head = ""
        code = 200
        try:
            request = HTTPRequest(data["readdata"])
        except Exception, e:
            res = "http format error: " + e.message
            code = 400
        headers = {}
        try:
            headers["Connection"] = "keep-alive"
            controller = vars.controller_dic.get(request.controller, None)
            controller = getattr(controller, request.controller)
            method = getattr(controller, request.action)
            res, new_headers = method(request)
            headers.update(new_headers)
        except Exception, e:
            print e, vars.backtrace()
            vars.logger.error(str(e) + vars.backtrace())
            res = "page not found"
            code = 404

        try:
            if headers.get("Connection", "") != "close":
                data["keepalive"] = True
            res_len = len(res)
            headers["Content-Length"] = res_len
            for key in headers:
                add_head += "%s: %s\r\n" % (key, headers[key])
            data["writedata"] = "HTTP/1.1 %s %s\r\n%s\r\n%s" % (code, res, add_head, res)
            data["readdata"] = ""
            epoll_fd.modify(fd, select.EPOLLET | select.EPOLLOUT | select.EPOLLERR | select.EPOLLHUP)
        except Exception, e:
            print str(e) + vars.backtrace()
