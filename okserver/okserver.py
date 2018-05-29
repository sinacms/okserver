import errno
import logging
import os
import re
import select
import socket
import sys
import time
from multiprocessing import cpu_count
import vars
import thread_pool
import multiprocessing
import signal


class Server:
    def __init__(self, forever_callback = None):
        if None == forever_callback:
            self.forever_callback = self.forever
        else:
            self.forever_callback = forever_callback

    def set_logger(self, logger):
        if None == logger:
            logger = logging.getLogger('okserver')
        vars.logger = logger

    def load_modules(self):
        path = vars.controller_dir
        for l in os.listdir(path):
            prefixname, extname = os.path.splitext(l)
            filepath = path + os.sep + prefixname
            module = re.sub('\.+', '.', re.sub('/+', '.', filepath)).strip('.')
            if extname == ".py" and prefixname != '__init__':
                vars.controller_time[prefixname] = os.path.getmtime(path + os.sep + l)
                vars.controller_dic[prefixname] = __import__(module)

    def start(self, host='', port=80, backlog=1024):
        reload(sys)
        sys.setdefaultencoding('utf8')
        self.load_modules()
        try:
            listen_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        except Exception, e:
            vars.logger.error("create socket failed: " + e.message)
        try:
            listen_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception, e:
            vars.logger.error("setsocketopt SO_REUSEADDR failed: " + e.message)
        try:
            listen_fd.bind((host, port))
        except Exception, e:
            vars.logger.error("bind failed: " + e.message)
            raise OSError("bind failed: " + e.message)
        try:
            listen_fd.listen(backlog)
            listen_fd.setblocking(0)
        except Exception, e:
            vars.logger.error(e)

        cpu_cores = cpu_count() * 2
        c = 0
        print 'master pid: ', os.getpid()
        self.forever_callback()
        _processes = []
        while c < cpu_cores:
            c += 1
            p = multiprocessing.Process(target=self.poll_connects, args=(listen_fd, ))
            p.start()
            _processes.append(p)
            # newpid = os.fork()
            # if 0 != newpid:
            #     self.poll_connects(listen_fd)
        for p in _processes:
            p.join()

    def poll_connects(self, listen_fd):
        print '\--child pid:  ', os.getpid()
        try:
            epoll_fd = select.epoll()
            epoll_fd.register(listen_fd.fileno(), select.EPOLLIN | select.EPOLLET | select.EPOLLERR | select.EPOLLHUP)
        except select.error, e:
            print e, vars.backtrace()
            vars.logger.error(e)

        tp = thread_pool.ThreadPool(4)
        tp.start()
        params = {}

        def clear_fd(fd):
            try:
                _param = params[fd]
                epoll_fd.unregister(fd)
                _param["connection"].close()
            except Exception, e:
                print e, vars.backtrace()
                pass

            if fd in params:
                del params[fd]
            # try:
            #     del params[fd]
            # except Exception, e:
            #     print e, vars.backtrace()
                # pass

        last_min_time = -1
        while True:
            epoll_list = epoll_fd.poll()

            for fd, events in epoll_list:
                cur_time = time.time()
                if fd == listen_fd.fileno():
                    while True:
                        try:

                            conn, addr = listen_fd.accept()
                            conn.setblocking(0)
                            epoll_fd.register(conn.fileno(),
                                              select.EPOLLIN | select.EPOLLET | select.EPOLLERR | select.EPOLLHUP)
                            conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                            # conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
                            params[conn.fileno()] = {"addr": addr, "writelen": 0, "connection": conn, "time": cur_time}
                        except socket.error, e:
                            break
                elif select.EPOLLIN & events:
                    param = params.get(fd, None)
                    if param is None:
                        continue
                    param["time"] = cur_time
                    datas = param.get("readdata", "")
                    cur_sock = params[fd]["connection"]
                    while True:
                        try:
                            data = cur_sock.recv(1024)
                            if not data:
                                clear_fd(fd)
                                break
                            else:
                                datas += data
                        except socket.error, e:
                            if e.errno == errno.EAGAIN:
                                param["readdata"] = datas
                                len_e = -1
                                contentlen = -1
                                headlen = -1
                                len_s = datas.find("Content-Length:")
                                if len_s > 0:
                                    len_e = datas.find("\r\n", len_s)
                                if len_s > 0 and len_e > 0 and len_e > len_s + 15:
                                    len_str = datas[len_s + 15:len_e].strip()
                                    if len_str.isdigit():
                                        contentlen = int(datas[len_s + 15:len_e].strip())
                                headend = datas.find("\r\n\r\n")
                                if headend > 0:
                                    headlen = headend + 4
                                data_len = len(datas)
                                if (contentlen > 0 and headlen > 0 and (contentlen + headlen) == data_len) or \
                                        (contentlen == -1 and headlen == data_len):
                                    tp.add_job(param, epoll_fd, fd)
                                break
                            else:
                                clear_fd(fd)
                                break
                elif select.EPOLLHUP & events or select.EPOLLERR & events:
                    clear_fd(fd)
                    vars.logger.error("sock: %s error" % fd)
                elif select.EPOLLOUT & events:
                    param = params.get(fd, None)
                    if param is None:
                        continue
                    param["time"] = cur_time
                    sendlen = param.get("writelen", 0)
                    writedata = param.get("writedata", "")
                    total_write_len = len(writedata)
                    cur_sock = param["connection"]
                    if writedata == "":
                        clear_fd(fd)
                        continue
                    while True:
                        try:
                            sendlen += cur_sock.send(writedata[sendlen:])
                            if sendlen == total_write_len:
                                if param.get("keepalive", True):
                                    param["readdata"] = ""
                                    param["writedata"] = ""
                                    param["writelen"] = 0
                                    epoll_fd.modify(fd,
                                                    select.EPOLLET | select.EPOLLIN | select.EPOLLERR | select.EPOLLHUP)
                                else:
                                    clear_fd(fd)
                                break
                        except socket.error, e:
                            print e, vars.backtrace()
                            if e.errno == errno.EAGAIN:
                                param["writelen"] = sendlen
                                break
                            clear_fd(fd)
                else:
                    continue
                # check time out
                if cur_time - last_min_time > vars.timeout_total:
                    last_min_time = cur_time
                    objs = params.items()
                    for (key_fd, value) in objs:
                        fd_time = value.get("time", 0)
                        del_time = cur_time - fd_time
                        if del_time > vars.timeout_total:
                            clear_fd(key_fd)
                        elif fd_time < last_min_time:
                            last_min_time = fd_time
