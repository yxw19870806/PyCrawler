# -*- coding:utf-8  -*-
"""
Instagram批量关注
https://www.instagram.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import os
import sys
import time

COOKIE_INFO = {}
IS_FOLLOW_PRIVATE_ACCOUNT = False  # 是否对私密账号发出关注请求


# 获取账号首页
def get_index_page(account_name):
    index_page_url = "https://www.instagram.com/%s" % account_name
    index_page_response = net.http_request(index_page_url, cookies_list=COOKIE_INFO)
    extra_info = {
        "account_id": None,  # 页面解析出的account id
        "is_follow": False,  # 是否已经关注
        "is_private": False,  # 是否是私密账号
    }
    if index_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        account_id = tool.find_sub_string(index_page_response.data, '"profilePage_', '"')
        if account_id and robot.is_integer(account_id):
            extra_info["account_id"] = account_id
        extra_info["is_follow"] = tool.find_sub_string(index_page_response.data, '"followed_by_viewer": ', ",") == "true"
        extra_info["is_private"] = tool.find_sub_string(index_page_response.data, '"is_private": ', ",") == "true"
    index_page_response.extra_info = extra_info
    return index_page_response


# 关注指定账号
def follow_account(account_name, account_id):
    follow_api_url = "https://www.instagram.com/web/friendships/%s/follow/" % account_id
    header_list = {"Referer": "https://www.instagram.com/", "x-csrftoken": COOKIE_INFO["csrftoken"], "X-Instagram-AJAX": 1}
    follow_api_response = net.http_request(follow_api_url, method="POST", header_list=header_list, cookies_list=COOKIE_INFO, json_decode=True)
    if follow_api_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if robot.check_sub_key(("status", "result"), follow_api_response.json_data):
            if follow_api_response.json_data["result"] == "following":
                tool.print_msg("关注%s成功" % account_name)
                return True
            elif follow_api_response.json_data["result"] == "requested":
                tool.print_msg("私密账号%s，已发送关注请求" % account_name)
                return True
            else:
                return False
        else:
            tool.print_msg("关注%s失败，返回内容：%s，退出程序！" % (account_name, follow_api_response.json_data))
            tool.process_exit()
    elif follow_api_response.status == 403 and follow_api_response.data == "Please wait a few minutes before you try again.":
        tool.print_msg("关注%s失败，连续关注太多等待一会儿继续尝试" % account_name)
        tool.process_exit()
    else:
        tool.print_msg("关注%s失败，请求返回结果：%s，退出程序！" % (account_name, robot.get_http_request_failed_reason(follow_api_response.status)))
        tool.process_exit()
    return False


if __name__ == "__main__":
    config = robot.read_config(os.path.join(os.path.dirname(sys._getframe().f_code.co_filename), "..\\common\\config.ini"))
    # 操作系统&浏览器
    browser_type = robot.get_config(config, "BROWSER_TYPE", 2, 1)
    # cookie
    is_auto_get_cookie = robot.get_config(config, "IS_AUTO_GET_COOKIE", True, 4)
    if is_auto_get_cookie:
        cookie_path = robot.tool.get_default_browser_cookie_path(browser_type)
    else:
        cookie_path = robot.get_config(config, "COOKIE_PATH", "", 0)
    all_cookie_from_browser = tool.get_all_cookie_from_browser(browser_type, cookie_path)
    if "www.instagram.com" in all_cookie_from_browser:
        for cookie_key in all_cookie_from_browser["www.instagram.com"]:
            COOKIE_INFO[cookie_key] = all_cookie_from_browser["www.instagram.com"][cookie_key]
    else:
        tool.print_msg("没有获取到登录信息，退出！")
        tool.process_exit()

    # 存档位置
    save_data_path = robot.get_config(config, "SAVE_DATA_PATH", "info/save.data", 3)
    # 读取存档文件
    account_list = robot.read_save_data(save_data_path, 0, [""])

    count = 0
    for account in sorted(account_list.keys()):
        account_page_response = get_index_page(account)
        if account_page_response.status == 404:
            log.error(account + " 账号不存在")
        elif account_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
            log.error(account + " 首页访问失败，原因：%s" % robot.get_http_request_failed_reason(account_page_response.status))
            break

        if account_page_response.extra_info["account_id"] is None:
            log.error(account + " account id解析失败")
            tool.process_exit()

        if account_page_response.extra_info["is_follow"]:
            tool.print_msg("%s已经关注，跳过" % account)
        elif account_page_response.extra_info["is_private"] and not IS_FOLLOW_PRIVATE_ACCOUNT:
            tool.print_msg("%s是私密账号，跳过" % account)
        else:
            if follow_account(account, account_page_response.extra_info["account_id"]):
                count += 1
            time.sleep(0.1)

    tool.print_msg("关注完成，成功关注了%s个账号" % count)
