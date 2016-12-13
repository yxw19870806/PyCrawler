# -*- coding:UTF-8  -*-
"""
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from multiprocessing.connection import Client, Listener
import threading


PROCESS_SERVER_IP = "localhost"  # 监听服务器IP
PROCESS_SERVER_PORT = 54321  # 监听服务器端口
PROCESS_STATUS = 0  # 服务器当前状态
PROCESS_STATUS_RUN = 0  # 进程运行中
PROCESS_STATUS_PAUSE = 1  # 进程暂停，知道状态变为0时才继续下载
PROCESS_STATUS_STOP = 2  # 进程立刻停止，删除还未完成的数据
PROCESS_STATUS_FINISH = 3  # 进程等待现有任务完成后停止
PROCESS_PID_LIST = []  # 存放所有需要操作的进程PID


# 进程监控
class ProcessControl(threading.Thread):
    def __init__(self, ip=PROCESS_SERVER_IP, port=PROCESS_SERVER_PORT):
        threading.Thread.__init__(self)
        self.ip = str(ip)
        self.port = int(port)

    def run(self):
        global PROCESS_STATUS
        listener = Listener((self.ip, self.port))
        while True:
            try:
                conn = listener.accept()
                new_status = int(conn.recv())
                if new_status in [PROCESS_STATUS_RUN, PROCESS_STATUS_PAUSE, PROCESS_STATUS_FINISH, PROCESS_STATUS_STOP]:
                    PROCESS_STATUS = new_status
            except IOError:
                pass
            finally:
                conn.close()
        listener.close()


# 设置进程状态
def set_process_status(process_status):
    try:
        process_status = int(process_status)
    except ValueError:
        process_status = PROCESS_STATUS_RUN
    except TypeError:
        process_status = PROCESS_STATUS_RUN
    conn = Client((PROCESS_SERVER_IP, PROCESS_SERVER_PORT))
    conn.send(process_status)


def pause_process():
    set_process_status(PROCESS_STATUS_PAUSE)


def continue_process():
    set_process_status(PROCESS_STATUS_RUN)
