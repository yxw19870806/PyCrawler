# -*- coding:UTF-8  -*-
"""
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
    if IS_SHOW_ERROR:
        msg = tool.get_time() + " [Error] " + msg
        tool.print_msg(msg, False)
    if ERROR_LOG_PATH != "":
        tool.write_file(msg, ERROR_LOG_PATH)


def step(msg):
    if IS_SHOW_STEP:
        msg = tool.get_time() + " " + msg
        tool.print_msg(msg, False)
    if STEP_LOG_PATH != "":
        tool.write_file(msg, STEP_LOG_PATH)


def trace(msg):
    if IS_SHOW_TRACE:
        msg = tool.get_time() + " " + msg
        tool.print_msg(msg, False)
    if TRACE_LOG_PATH != "":
        tool.write_file(msg, TRACE_LOG_PATH)
