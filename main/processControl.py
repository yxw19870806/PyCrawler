# -*- coding:UTF-8  -*-
"""
向监听端口发送指定指令
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from multiprocessing.connection import Client
from common import crawler, portListenerEvent


class ProcessControl():
    def __init__(self):
        config = crawler._get_config()
        server_port = crawler.analysis_config(config, "LISTENER_PORT", 0, crawler.CONFIG_ANALYSIS_MODE_INTEGER)
        self.conn = Client((portListenerEvent.SERVER_IP, server_port))

    def send_code(self, process_status):
        self.conn.send(int(process_status))
