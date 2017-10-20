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


# 控制台输出
# thread_lock   threading.Lock()，传入锁保证线程安全
def print_msg(msg, is_time=True):
    if is_time:
        msg = _get_time() + " " + msg
    thread_lock.acquire()
    try:
        # 终端输出编码
        output_encoding = sys.stdout.encoding
        if output_encoding == "UTF-8":
            print msg
        else:
            print msg.decode("UTF-8").encode(output_encoding)
    except UnicodeEncodeError:
        print msg
    except:
        raise
    finally:
        thread_lock.release()


# 控制台输入
def console_input(msg):
    output_encoding = sys.stdout.encoding
    if output_encoding != "UTF-8":
        msg = msg.decode("UTF-8").encode(output_encoding)
    return raw_input(msg)


# 获取时间
def _get_time():
    return time.strftime("%m-%d %H:%M:%S", time.localtime(time.time()))
