import Queue
import threading
from mythread import Thread


class ThreadPool:
    def __init__(self, num_of_threads=4):
        self.thread_condition = threading.Condition()
        self.share_object = Queue.Queue()
        self.threads = []
        self.add_to_pool(num_of_threads)

    def add_to_pool(self, num_of_threads):
        for i in range(num_of_threads):
            thread = Thread(self.thread_condition, self.share_object)
            self.threads.append(thread)

    def start(self):
        for thread in self.threads:
            thread.start()

    def add_job(self, *args, **kwargs):
        self.share_object.put((args, kwargs))
