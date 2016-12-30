# -*- coding:UTF-8  -*-
"""
日志写入类
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import tool

IS_SHOW_ERROR = True
IS_SHOW_STEP = False
IS_SHOW_TRACE = False
ERROR_LOG_PATH = ""
STEP_LOG_PATH = ""
TRACE_LOG_PATH = ""


def error(msg):
    msg = tool.get_time() + " [Error] " + msg
    if IS_SHOW_ERROR:
        tool.print_msg(msg, False)
    if ERROR_LOG_PATH != "":
        tool.write_file(msg, ERROR_LOG_PATH)


def step(msg):
    msg = tool.get_time() + " " + msg
    if IS_SHOW_STEP:
        tool.print_msg(msg, False)
    if STEP_LOG_PATH != "":
        tool.write_file(msg, STEP_LOG_PATH)


def trace(msg):
    msg = tool.get_time() + " " + msg
    if IS_SHOW_TRACE:
        tool.print_msg(msg, False)
    if TRACE_LOG_PATH != "":
        tool.write_file(msg, TRACE_LOG_PATH)
