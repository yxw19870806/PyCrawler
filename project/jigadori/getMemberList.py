# -*- coding:UTF-8  -*-
"""
グラドル自画撮り部 成员tweet账号获取
http://jigadori.fkoji.com/users
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import os
from pyquery import PyQuery as pq
from common import *

# Twitter存档文件目录
SAVE_DATA_PATH = os.path.abspath(os.path.join(tool.PROJECT_APP_ROOT_PATH, "twitter/info/save_5.data"))


# 获取存档文件
def get_account_from_save_data():
    account_list = {}
    if not os.path.exists(SAVE_DATA_PATH):
        return account_list
    for line in tool.read_file(SAVE_DATA_PATH, tool.READ_FILE_TYPE_LINE):
        line = line.replace("\n", "")
        account_info_temp = line.split("\t")
        account_list[account_info_temp[0]] = line
    return account_list


# 从页面获取全部账号
def get_account_from_index():
    page_count = 1
    account_list = {}
    while True:
        try:
            pagination_account_list = get_one_page_account(page_count)
        except crawler.CrawlerException, e:
            output.print_msg("第%s页账号解析失败，原因：%s" % (page_count, e.message))
        if len(pagination_account_list) > 0:
            account_list.update(pagination_account_list)
            page_count += 1
        else:
            break
    return account_list


# 获取一页账号
def get_one_page_account(page_count):
    account_pagination_url = "http://jigadori.fkoji.com/users"
    query_data = {"p": page_count}
    account_pagination_response = net.http_request(account_pagination_url, method="GET", fields=query_data)
    pagination_account_list = {}
    if account_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        crawler.CrawlerException(crawler.request_failre(account_pagination_response.status))
    account_list_selector = pq(account_pagination_response.data.decode("UTF-8")).find(".users-list li")
    for account_index in range(0, account_list_selector.length):
        account_selector = account_list_selector.eq(account_index)
        # 获取成员名字
        account_name = account_selector.find(".profile-name").eq(0).text()
        if not account_name:
            account_name = ""
            # raise robot.CrawlerException("成员信息截取成员名字失败\n\%s" % account_selector.html().encode("UTF-8"))
        else:
            account_name = account_name.strip().encode("UTF-8")
        # 获取twitter账号
        account_id = account_selector.find(".screen-name a").text()
        if not account_id:
            raise crawler.CrawlerException("成员信息截取twitter账号失败\n\%s" % account_selector.html().encode("UTF-8"))
        account_id = account_id.strip().replace("@", "")
        pagination_account_list[account_id] = account_name
    return pagination_account_list


def main():
    account_list_from_api = get_account_from_index()
    if len(account_list_from_api) > 0:
        account_list_from_save_data = get_account_from_save_data()
        for account_id in account_list_from_save_data:
            if account_id not in account_list_from_api:
                output.print_msg("%s (%s) not found from API result" % (account_id, account_list_from_save_data[account_id]))
        for account_id in account_list_from_api:
            if account_id not in account_list_from_save_data:
                account_list_from_save_data[account_id] = "%s\t\t\t\t\t%s" % (account_id, account_list_from_api[account_id])
            else:
                temp_list = account_list_from_save_data[account_id].split("\t")
                if len(temp_list) >= 6 and temp_list[5] != account_list_from_api[account_id]:
                    output.print_msg("%s name changed" % account_id)
                    account_list_from_save_data[account_id] = "\t".join(temp_list)
        temp_list = [account_list_from_save_data[key] for key in sorted(account_list_from_save_data.keys())]
        tool.write_file("\n".join(temp_list), SAVE_DATA_PATH, tool.WRITE_FILE_TYPE_REPLACE)


if __name__ == "__main__":
    main()
