import logging
import traceback
import sys

controller_dic = {}
controller_time = {}
timeout_total = 10
logger = logging.getLogger("okserver")
controller_dir = 'controller'


def backtrace():
    tb = sys.exc_info()[2]
    msg = ''
    for i in traceback.format_tb(tb):
        msg += i
    return msg