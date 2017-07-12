# -*- coding:UTF-8  -*-
"""
グラドル自画撮り部 成员tweet账号获取
http://jigadori.fkoji.com/users
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import net, tool
from pyquery import PyQuery as pq
import os


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


# 从页面获取全部账号
def get_account_from_index():
    page_count = 1
    account_list = {}
    while True:
        pagination_account_list = get_one_page_account(page_count)
        if len(pagination_account_list) > 0:
            account_list.update(pagination_account_list)
            page_count += 1
        else:
            break
    return account_list


# 获取一页账号
def get_one_page_account(page_count):
    account_pagination_url = "http://jigadori.fkoji.com/users?p=%s" % page_count
    account_pagination_response = net.http_request(account_pagination_url)
    pagination_account_list = {}
    if account_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        account_list_selector = pq(account_pagination_response.data.decode("UTF-8")).find(".users-list li")
        for account_index in range(0, account_list_selector.size()):
            account_selector = account_list_selector.eq(account_index)
            account_name = account_selector.find(".profile-name").eq(0).text()
            account_id = account_selector.find(".screen-name a").text()
            if account_name and account_id:
                account_id = account_id.strip().replace("@", "")
                account_name = account_name.strip().encode("UTF-8")
                pagination_account_list[account_id] = account_name
    return pagination_account_list


def main():
    save_data_path = os.path.join("../twitter/info/save_5.data")
    account_list_from_api = get_account_from_index()
    if len(account_list_from_api) > 0:
        account_list_from_save_data = get_account_from_save_data(save_data_path)
        for account_id in account_list_from_api:
            if account_id not in account_list_from_save_data:
                account_list_from_save_data[account_id] = "%s\t\t\t\t\t%s" % (account_id, account_list_from_api[account_id])
        temp_list = [account_list_from_save_data[key] for key in sorted(account_list_from_save_data.keys())]
        tool.write_file(tool.list_to_string(temp_list, "\n", ""), save_data_path, 2)


if __name__ == "__main__":
    main()
