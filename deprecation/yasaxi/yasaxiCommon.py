# -*- coding:UTF-8  -*-
"""
看了又看APP图片爬虫
http://share.yasaxi.com/share.html
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import json
import os
from common import *

ACCESS_TOKEN = ""
AUTH_TOKEN = ""
ZHEZHE_INFO = ""
account_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "session"))


# 从文件中获取用户信息
def get_token_from_file():
    account_data = tool.json_decode(tool.decrypt_string(tool.read_file(account_file_path)))
    if account_data is None:
        return False
    if crawler.check_sub_key(("access_token", "auth_token", "zhezhe_info"), account_data):
        global ACCESS_TOKEN
        global AUTH_TOKEN
        global ZHEZHE_INFO
        ACCESS_TOKEN = account_data["access_token"]
        AUTH_TOKEN = account_data["auth_token"]
        ZHEZHE_INFO = account_data["zhezhe_info"]
        return True
    return False


# 输入token并加密保存到文件中
def set_token_to_file():
    access_token = output.console_input("access_token: ")
    auth_token = output.console_input("auth_token: ")
    zhezhe_info = output.console_input("zhezhe_info: ")
    account_data = {
        "access_token": access_token,
        "auth_token": auth_token,
        "zhezhe_info": zhezhe_info,
    }
    tool.write_file(tool.encrypt_string(json.dumps(account_data)), account_file_path, tool.WRITE_FILE_TYPE_REPLACE)
