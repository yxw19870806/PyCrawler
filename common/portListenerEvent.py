# -*- coding:UTF-8  -*-
"""
端口监控类
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import threading
from multiprocessing.connection import Listener

SERVER_IP = "localhost"  # 监听服务器IP
PROCESS_STATUS_RUN = 0  # 进程运行中
PROCESS_STATUS_PAUSE = 1  # 进程暂停，知道状态变为0时才继续下载
PROCESS_STATUS_STOP = 2  # 进程立刻停止，删除还未完成的数据


class PortListenerEvent(threading.Thread):
    """program status controller Class"""
    def __init__(self, port, event_list=None):
        threading.Thread.__init__(self)
        self.ip = SERVER_IP
        self.port = int(port)
        self.event_list = event_list

    def run(self):
        listener = Listener((self.ip, self.port))
        while True:
            try:
                conn = listener.accept()
                command = conn.recv()
                if self.event_list and command in self.event_list:
                    self.event_list[command]()
            except IOError:
                pass
            finally:
                conn.close()
        listener.close()
