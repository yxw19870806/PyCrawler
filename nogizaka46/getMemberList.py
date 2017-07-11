# -*- coding:UTF-8  -*-
"""
乃木坂46 OFFICIAL BLOG成员id获取
http://http://blog.nogizaka46.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import net, tool
import os
import re


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


# 从页面获取全部成员账号
def get_account_from_index():
    index_url = "http://blog.nogizaka46.com/"
    index_response = net.http_request(index_url)
    account_list = {}
    if index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        member_list_find = re.findall('<div class="unit"><a href="./([^"]*)"><img src="[^>]*alt="([^"]*)" />', index_response.data)
        for member_info in member_list_find:
            account_list[member_info[0]] = member_info[1].replace(" ", "")
    return account_list


def main():
    save_data_path = os.path.join("info/save.data")
    account_list_from_api = get_account_from_index()
    if len(account_list_from_api) > 0:
        account_list_from_save_data = get_account_from_save_data(save_data_path)
        for account_id in account_list_from_api:
            if account_id not in account_list_from_save_data:
                account_list_from_save_data[account_id] = "%s\t\t\t%s" % (account_id, account_list_from_api[account_id])
        temp_list = [account_list_from_save_data[key] for key in sorted(account_list_from_save_data.keys())]
        tool.write_file(tool.list_to_string(temp_list, "\n", ""), save_data_path, 2)

if __name__ == "__main__":
    main()
