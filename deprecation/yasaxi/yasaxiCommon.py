# -*- coding:UTF-8  -*-
"""
看了又看APP图片爬虫
http://share.yasaxi.com/share.html
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import base64
import json
import os
import sys

ACCESS_TOKEN = ""
AUTH_TOKEN = ""
ZHEZHE_INFO = ""


# 从文件中获取用户信息
def get_token_from_file():
    account_file_path = os.path.realpath(os.path.join(os.path.dirname(sys._getframe().f_code.co_filename), "token.data"))
    try:
        account_data = json.loads(base64.b64decode(tool.read_file(account_file_path)))
    except TypeError:
        return False
    except ValueError:
        return False
    if robot.check_sub_key(("access_token", "auth_token", "zhezhe_info"), account_data):
        global ACCESS_TOKEN
        global AUTH_TOKEN
        global ZHEZHE_INFO
        ACCESS_TOKEN = account_data["access_token"]
        AUTH_TOKEN = account_data["auth_token"]
        ZHEZHE_INFO = account_data["zhezhe_info"]
        return True
    return False
