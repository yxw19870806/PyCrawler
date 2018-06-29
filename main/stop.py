# -*- coding:UTF-8  -*-
"""
结束所有爬虫程序
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import portListenerEvent
import processControl


if __name__ == "__main__":
    processControl.ProcessControl().send_code(portListenerEvent.PROCESS_STATUS_STOP)
