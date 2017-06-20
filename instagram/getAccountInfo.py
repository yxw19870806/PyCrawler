# -*- coding:utf-8  -*-
"""
Instagram批量获取账号介绍
https://www.instagram.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import os
import sys


# 获取账号首页
def get_index_page(account_name):
    index_page_url = "https://www.instagram.com/%s/?hl=zh-cn" % account_name
    index_page_response = net.http_request(index_page_url)
    extra_info = {
        "account_info": "",  # 页面解析出的自我介绍
        "external_url": "",  # 页面解析出的外部地址
    }
    if index_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        account_info = tool.find_sub_string(index_page_response.data, '"biography": "', '"')
        if account_info:
            account_info = account_info.replace(r"\n", "").replace("'", chr(1))
            account_info = eval("u'%s'" % account_info).replace(chr(1), "'").encode("utf-8")
            extra_info["account_info"] = account_info
        extra_info["external_url"] = tool.find_sub_string(index_page_response.data, '"external_url": "', '"')
    index_page_response.extra_info = extra_info
    return index_page_response


if __name__ == "__main__":
    config = robot.read_config(os.path.join(os.path.dirname(sys._getframe().f_code.co_filename), "..\\common\\config.ini"))
    # 存档位置
    save_data_path = robot.get_config(config, "SAVE_DATA_PATH", "info/save.data", 3)
    # 读取存档文件
    account_list = robot.read_save_data(save_data_path, 0, [""])

    result_file_path = "info/account_info.data"
    for account in sorted(account_list.keys()):
        account_page_response = get_index_page(account)
        if account_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            tool.write_file("%s\t%s\t%s" % (account, account_page_response.extra_info["account_info"], account_page_response.extra_info["external_url"]), result_file_path)
