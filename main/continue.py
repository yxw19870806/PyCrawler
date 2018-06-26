# -*- coding:UTF-8  -*-
"""
继续所有已经暂停的爬虫程序
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import portListenerEvent
from . import processControl


if __name__ == "__main__":
    processControl.ProcessControl().send_code(portListenerEvent.PROCESS_STATUS_RUN)
