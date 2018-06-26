# -*- coding:UTF-8  -*-
"""
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import threading
from multiprocessing.connection import Client, Listener

PROCESS_SERVER_IP = "localhost"  # 监听服务器IP
PROCESS_SERVER_PORT = 12345  # 监听服务器端口
PROCESS_STATUS_RUN = 0  # 进程运行中
PROCESS_STATUS_PAUSE = 1  # 进程暂停，知道状态变为0时才继续下载
PROCESS_STATUS_STOP = 2  # 进程立刻停止，删除还未完成的数据


class ProcessControl(threading.Thread):
    """program status controller Class"""
    def __init__(self, port=PROCESS_SERVER_PORT, event_list=None):
        threading.Thread.__init__(self)
        self.ip = PROCESS_SERVER_IP
        self.port = int(port)
        self.event_list = event_list

    def run(self):
        listener = Listener((self.ip, self.port))
        while True:
            try:
                conn = listener.accept()
                command = int(conn.recv())
                if command in self.event_list:
                    self.event_list[command]()
            except IOError:
                pass
            finally:
                conn.close()
        listener.close()


def set_process_status(process_status):
    """Set program status"""
    try:
        process_status = int(process_status)
    except ValueError:
        process_status = PROCESS_STATUS_RUN
    except TypeError:
        process_status = PROCESS_STATUS_RUN
    conn = Client((PROCESS_SERVER_IP, PROCESS_SERVER_PORT))
    conn.send(process_status)


def pause_process():
    """Pause program"""
    set_process_status(PROCESS_STATUS_PAUSE)


def continue_process():
    """restart program"""
    set_process_status(PROCESS_STATUS_RUN)


def stop_process():
    """Stop program"""
    set_process_status(PROCESS_STATUS_STOP)
