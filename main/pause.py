# -*- coding:UTF-8  -*-
"""
暂停所有正在运行的爬虫程序
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import process, tool

process.set_process_status(tool.ProcessControl.PROCESS_PAUSE)