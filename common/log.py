# -*- coding:UTF-8  -*-
"""
日志写入类
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import tool
import threading

IS_SHOW_ERROR = True
IS_SHOW_STEP = False
IS_SHOW_TRACE = False
ERROR_LOG_PATH = ""
STEP_LOG_PATH = ""
TRACE_LOG_PATH = ""
thread_lock = threading.Lock()


def error(msg):
    msg = tool.get_time() + " [Error] " + str(msg)
    if IS_SHOW_ERROR:
        tool.print_msg(msg, False)
    if ERROR_LOG_PATH != "":
        thread_lock.acquire()
        try:
            tool.write_file(msg, ERROR_LOG_PATH)
        except:
            raise
        finally:
            thread_lock.release()


def step(msg):
    msg = tool.get_time() + " " + str(msg)
    if IS_SHOW_STEP:
        tool.print_msg(msg, False)
    if STEP_LOG_PATH != "":
        thread_lock.acquire()
        try:
            tool.write_file(msg, STEP_LOG_PATH)
        except:
            raise
        finally:
            thread_lock.release()


def trace(msg):
    msg = tool.get_time() + " " + str(msg)
    if IS_SHOW_TRACE:
        tool.print_msg(msg, False)
    if TRACE_LOG_PATH != "":
        thread_lock.acquire()
        try:
            tool.write_file(msg, TRACE_LOG_PATH)
        except:
            raise
        finally:
            thread_lock.release()
