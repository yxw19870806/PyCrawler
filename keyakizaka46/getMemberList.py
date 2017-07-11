# -*- coding:UTF-8  -*-
"""
欅坂46公式ブログ成员id获取
http://www.keyakizaka46.com/mob/news/diarShw.php?cd=member
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
    index_url = "http://www.keyakizaka46.com/mob/news/diarShw.php?cd=member"
    index_response = net.http_request(index_url)
    account_list = {}
    if index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        member_list_data = tool.find_sub_string(index_response.data, '<ul class="thumb">', "</ul>")
        if member_list_data:
            member_list_find = re.findall("<li ([\S|\s]*?)</li>", member_list_data)
            for member_info in member_list_find:
                account_id = tool.find_sub_string(member_info, "&ct=", '">')
                account_name = tool.find_sub_string(member_info, '<p class="name">', "</p>").strip().replace(" ", "")
                account_list[account_id] = account_name
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
