# -*- coding:UTF-8  -*-
"""
7gogo批量获取账号所参与的全部talk id
https://7gogo.jp/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
from pyquery import PyQuery as PQ
import os
import sys

# 存放账号的文件路径
ACCOUNT_ID_FILE_PATH = os.path.join(os.path.dirname(sys._getframe().f_code.co_filename), "info/account.data")
# 存放解析出的账号文件路径
TALK_ID_FILE_PATH = os.path.join(os.path.dirname(sys._getframe().f_code.co_filename), "info/talk.data")


# 获取account id文件
def get_account_from_file():
    account_list = {}
    for line in tool.read_file(ACCOUNT_ID_FILE_PATH, 2):
        split_temp = line.replace("\n", "").split("\t")
        account_list[split_temp[0]] = split_temp[1]
    return account_list


# 根据talk id获取全部参与者
def get_account_talks(account_id, account_name, talk_list):
    account_index = "https://7gogo.jp/users/%s" % account_id
    account_index_response = net.http_request(account_index, method="GET")
    if account_index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(account_index_response.status))
    talk_list_selector = PQ(account_index_response.data.decode("UTF-8")).find(".UserTalkWrapper .UserTalk")
    for talk_index in range(0, talk_list_selector.size()):
        talk_selector = talk_list_selector.eq(talk_index)
        # 获取talk地址
        talk_url_path = talk_selector.attr("href")
        if not talk_url_path:
            raise robot.RobotException("talk信息截取talk地址失败\n%s" % talk_selector.html.encode("UTF-8"))
        talk_id = str(talk_url_path.replace("/", ""))
        if not talk_id:
            raise robot.RobotException("talk地址截取talk id失败\n%s" % talk_url_path)
        # 获取talk名字
        talk_name = talk_selector.find(".UserTalk__talkname").text()
        if not talk_name:
            raise robot.RobotException("talk信息截取talk名字失败\n%s" % talk_selector.html.encode("UTF-8"))
        talk_name = robot.filter_emoji(str(talk_name.encode("UTF-8")).strip())
        # 获取talk描述
        talk_description = robot.filter_emoji(talk_selector.find(".UserTalk__description").text())
        if talk_description:
            talk_description = robot.filter_emoji(str(talk_description.encode("UTF-8")).strip())
        else:
            talk_description = ""
        if talk_id in talk_list:
            talk_list[talk_id]["account_list"].append(account_name)
        else:
            talk_list[talk_id] = {
                "account_list": [account_name],
                "talk_name": talk_name,
                "talk_description": talk_description,
            }
        output.print_msg(account_id + ": " + talk_name + ", " + talk_description)


def main():
    account_list = get_account_from_file()
    talk_list = {}
    for account_id in account_list:
        try:
            get_account_talks(account_id, account_list[account_id], talk_list)
        except robot.RobotException, e:
            output.print_msg(account_id + " 获取talk列表失败，原因：%s" % e.message)
    if len(talk_list) > 0:
        with open(TALK_ID_FILE_PATH, "w") as file_handle:
            for talk_id in talk_list:
                file_handle.write("%s\t%s\t%s\t%s\n" % (talk_id, talk_list[talk_id]["talk_name"], talk_list[talk_id]["talk_description"], " & ".join(talk_list[talk_id]["account_list"])))


if __name__ == "__main__":
    main()
