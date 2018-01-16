# -*- coding:UTF-8  -*-
"""

@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import sys
import threading
import time

thread_lock = threading.Lock()


def print_msg(msg, is_time=True):
    """Console print decoded message(according to coding of sys.stdout.encoding), thread safe"""
    try:
        # 终端输出编码
        output_encoding = sys.stdout.encoding
        if output_encoding == "UTF-8":
            msg = str(msg)
        else:
            msg = msg.decode("UTF-8").encode(output_encoding)
    except UnicodeEncodeError:
        pass
    else:
        if is_time:
            msg = _get_time() + " " + msg
    with thread_lock:
        print msg


def console_input(msg):
    """Console input"""
    output_encoding = sys.stdout.encoding
    if output_encoding != "UTF-8":
        msg = msg.decode("UTF-8").encode(output_encoding)
    return raw_input(msg)


def _get_time():
    """Get formatted time string(%m-%d %H:%M:%S)"""
    return time.strftime("%m-%d %H:%M:%S", time.localtime(time.time()))
