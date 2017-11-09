# -*- coding:UTF-8  -*-
"""
日志写入类
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import output, tool
import threading
import time

IS_SHOW_ERROR = True
IS_SHOW_STEP = False
IS_SHOW_TRACE = False
ERROR_LOG_PATH = ""
STEP_LOG_PATH = ""
TRACE_LOG_PATH = ""
thread_lock = threading.Lock()


def error(msg):
    """Error message logger"""
    msg = _get_time() + " [Error] " + str(msg)
    if IS_SHOW_ERROR:
        output.print_msg(msg, False)
    if ERROR_LOG_PATH != "":
        with thread_lock:
            tool.write_file(msg, ERROR_LOG_PATH)


def step(msg):
    """Step message logger"""
    msg = _get_time() + " " + str(msg)
    if IS_SHOW_STEP:
        output.print_msg(msg, False)
    if STEP_LOG_PATH != "":
        with thread_lock:
            tool.write_file(msg, STEP_LOG_PATH)


def trace(msg):
    """Trace(Debugger) message logger"""
    msg = _get_time() + " " + str(msg)
    if IS_SHOW_TRACE:
        output.print_msg(msg, False)
    if TRACE_LOG_PATH != "":
        with thread_lock:
            tool.write_file(msg, TRACE_LOG_PATH)


def _get_time():
    """Get formatted time string(%m-%d %H:%M:%S)"""
    return time.strftime("%m-%d %H:%M:%S", time.localtime(time.time()))
