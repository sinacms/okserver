import threading

import os

from connect_consumer import Worker
from vars import backtrace
import Queue


class Thread(threading.Thread):
    ind = 0

    def __init__(self, thread_condition, share_object, **kwargs):
        threading.Thread.__init__(self, kwargs=kwargs)
        self.thread_condition = thread_condition
        self.share_object = share_object
        self.setDaemon(True)
        self.worker = Worker()
        print '\----thread id', os.getpid(), threading.currentThread()

    def processer(self, args, kwargs):
        try:
            param = args[0]
            epoll_fd = args[1]
            fd = args[2]
            self.worker.process(param, epoll_fd, fd)
        except:
            print "job error:" + backtrace()

    def run(self):
        while True:
            try:
                args, kwargs = self.share_object.get()
                self.processer(args, kwargs)
            except Queue.Empty:
                continue
            except:
                print "thread error:" + backtrace()
