# -*- coding:UTF-8  -*-
"""
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from multiprocessing.connection import Client
from common import tool


def set_process_status(process_status):
    process_status = int(process_status)
    try:
        process_status = int(process_status)
    except ValueError:
        process_status = tool.ProcessControl.PROCESS_RUN
    except TypeError:
        process_status = tool.ProcessControl.PROCESS_RUN
    conn = Client((tool.PROCESS_CONTROL_IP, tool.PROCESS_CONTROL_PORT))
    conn.send(process_status)
