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
import sys


AUTH_TOKEN = ""
ZHEZHE_INFO = ""


# 从文件中获取用户信息
def get_token_from_file():
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


# 获取存档文件
def get_account_from_save_data(file_path):
    file_handle = open(file_path, "r")
    lines = file_handle.readlines()
    file_handle.close()
    account_list = {}
    for line in lines:
        line = line.replace("\n", "")
        account_info_temp = line.split("\t")
        account_list[account_info_temp[0]] = line
    return account_list


# 调用推荐API获取所有推荐账号
def get_account_from_api():
    api_url = "https://api.yasaxi.com/users/recommend?tag="
    header_list = {
        "x-auth-token": AUTH_TOKEN,
        "x-zhezhe-info": ZHEZHE_INFO,
    }
    account_list = {}
    api_response = net.http_request(api_url, header_list=header_list, json_decode=True)
    if api_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if robot.check_sub_key(("data",), api_response.json_data):
            for account_info in api_response.json_data["data"]:
                account_list[str(account_info["userId"].encode("UTF-8"))] = str(robot.filter_emoji(account_info["nick"]).encode("UTF-8")).strip()
    return account_list


def main():
    if get_token_from_file():
        config = robot.read_config(os.path.join(os.path.dirname(sys._getframe().f_code.co_filename), "..\\common\\config.ini"))
        # 存档位置
        save_data_path = robot.get_config(config, "SAVE_DATA_PATH", "info/save.data", 3)
        account_list_from_api = get_account_from_api()
        if len(account_list_from_api) > 0:
            account_list_from_save_data = get_account_from_save_data(save_data_path)
            for account_id in account_list_from_api:
                if account_id not in account_list_from_save_data:
                    account_list_from_save_data[account_id] = "%s\t\t%s" % (account_id, account_list_from_api[account_id])
            temp_list = [account_list_from_save_data[key] for key in sorted(account_list_from_save_data.keys())]
            tool.write_file(tool.list_to_string(temp_list, "\n", ""), save_data_path, 2)

if __name__ == "__main__":
    main()
