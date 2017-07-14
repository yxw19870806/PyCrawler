# -*- coding:UTF-8  -*-
"""
7gogo批量获取参与talk的账号
https://www.instagram.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import json
import os
import sys

COOKIE_INFO = {}
# 存放解析出的账号文件路径
ACCOUNT_ID_FILE_PATH = os.path.join("info/account.data")


# 获取存档文件
def get_account_from_save_data(file_path):
    account_list = {}
    if not os.path.exists(file_path):
        return account_list
    file_handle = open(file_path, "r")
    lines = file_handle.readlines()
    file_handle.close()
    for line in lines:
        line = line.replace("\n", "")
        account_info_temp = line.split("\t")
        account_list[account_info_temp[0]] = line
    return account_list


# 根据talk id获取全部参与者
def get_member_from_talk(talk_id):
    talk_index_url = "https://7gogo.jp/%s" % talk_id
    talk_index_response = net.http_request(talk_index_url)
    account_list = {}
    if talk_index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        talk_data_string = tool.find_sub_string(talk_index_response.data, "window.__STATES__ = ", "</script>")
        talk_data = None
        if talk_data_string:
            try:
                talk_data = json.loads(talk_data_string)
            except ValueError:
                pass
        if talk_data is not None:
            if robot.check_sub_key(("TalkStore",), talk_data) and robot.check_sub_key(("memberList",), talk_data["TalkStore"]):
                for member_info in talk_data["TalkStore"]["memberList"]:
                    account_list[str(member_info["userId"])] = str(member_info["name"].encode("UTF-8")).replace(" ", "")
    return account_list


def main():
    config = robot.read_config(os.path.join(os.path.dirname(sys._getframe().f_code.co_filename), "..\\common\\config.ini"))
    # 存档位置
    save_data_path = robot.get_config(config, "SAVE_DATA_PATH", "info/save.data", 3)
    account_list_from_save_data = get_account_from_save_data(save_data_path)
    account_list = []
    for talk_id in account_list_from_save_data:
        member_list = get_member_from_talk(talk_id)
        for account_id in member_list:
            if account_id not in account_list:
                print account_id, member_list[account_id]
                tool.write_file("%s\t%s" % (account_id, member_list[account_id]), ACCOUNT_ID_FILE_PATH, 1)
                account_list.append(account_id)


if __name__ == "__main__":
    main()