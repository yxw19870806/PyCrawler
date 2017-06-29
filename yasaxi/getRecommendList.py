# -*- coding:UTF-8  -*-
"""
看了又看APP全推荐账号获取
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import base64
import json
import os


AUTH_TOKEN = ""
ZHEZHE_INFO = ""


# 从文件中获取用户信息
def get_account_info_from_file():
    account_file_path = os.path.realpath("account.data")
    if not os.path.exists(account_file_path):
        return False
    file_handle = open(account_file_path, "r")
    file_string = file_handle.read()
    file_handle.close()
    file_string.replace("\n", "")
    try:
        account_data = json.loads(base64.b64decode(file_string))
    except TypeError:
        return False
    except ValueError:
        return False
    if robot.check_sub_key(("access_token", "auth_token", "zhezhe_info"), account_data):
        global AUTH_TOKEN
        global ZHEZHE_INFO
        AUTH_TOKEN = account_data["auth_token"]
        ZHEZHE_INFO = account_data["zhezhe_info"]
        return True
    return False


def get_recommend():
    api_url = "https://api.yasaxi.com/users/recommend?tag="
    header_list = {
        "x-auth-token": AUTH_TOKEN,
        "x-zhezhe-info": ZHEZHE_INFO,
    }
    api_response = net.http_request(api_url, header_list=header_list, json_decode=True)
    if api_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if robot.check_sub_key(("data",), api_response.json_data):
            for account_info in api_response.json_data["data"]:
                print "%s\t%s" % (str(account_info["userId"].encode("utf-8")), str(robot.filter_emoji(account_info["nick"]).encode("utf-8")).strip())

if __name__ == "__main__":
    get_account_info_from_file() and get_recommend()
