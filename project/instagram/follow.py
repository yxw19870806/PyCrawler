# -*- coding:UTF-8  -*-
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
def get_account_index_page(account_name):
    account_index_url = "https://www.instagram.com/%s" % account_name
    account_index_response = net.http_request(account_index_url, cookies_list=COOKIE_INFO)
    extra_info = {
        "account_id": None,  # 页面解析出的account id
        "is_follow": False,  # 是否已经关注
        "is_private": False,  # 是否是私密账号
    }
    if account_index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        account_id = tool.find_sub_string(account_index_response.data, '"profilePage_', '"')
        if account_id and robot.is_integer(account_id):
            extra_info["account_id"] = account_id
        extra_info["is_follow"] = tool.find_sub_string(account_index_response.data, '"followed_by_viewer": ', ",") == "true"
        extra_info["is_private"] = tool.find_sub_string(account_index_response.data, '"is_private": ', ",") == "true"
    account_index_response.extra_info = extra_info
    return account_index_response


# 关注指定账号
def follow_account(account_name, account_id):
    follow_api_url = "https://www.instagram.com/web/friendships/%s/follow/" % account_id
    header_list = {"Referer": "https://www.instagram.com/", "x-csrftoken": COOKIE_INFO["csrftoken"], "X-Instagram-AJAX": 1}
    follow_response = net.http_request(follow_api_url, method="POST", header_list=header_list, cookies_list=COOKIE_INFO, json_decode=True)
    if follow_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if robot.check_sub_key(("status", "result"), follow_response.json_data):
            if follow_response.json_data["result"] == "following":
                tool.print_msg("关注%s成功" % account_name)
                return True
            elif follow_response.json_data["result"] == "requested":
                tool.print_msg("私密账号%s，已发送关注请求" % account_name)
                return True
            else:
                return False
        else:
            tool.print_msg("关注%s失败，返回内容：%s，退出程序！" % (account_name, follow_response.json_data))
            tool.process_exit()
    elif follow_response.status == 403 and follow_response.data == "Please wait a few minutes before you try again.":
        tool.print_msg("关注%s失败，连续关注太多等待一会儿继续尝试" % account_name)
        tool.process_exit()
    else:
        tool.print_msg("关注%s失败，请求返回结果：%s，退出程序！" % (account_name, robot.get_http_request_failed_reason(follow_response.status)))
        tool.process_exit()
    return False


def main():
    config = robot.read_config(tool.PROJECT_CONFIG_PATH)
    # 操作系统&浏览器
    browser_type = robot.get_config(config, "BROWSER_TYPE", 2, 1)
    # cookie
    is_auto_get_cookie = robot.get_config(config, "IS_AUTO_GET_COOKIE", True, 4)
    if is_auto_get_cookie:
        cookie_path = tool.get_default_browser_cookie_path(browser_type)
    else:
        cookie_path = robot.get_config(config, "COOKIE_PATH", "", 0)
    all_cookie_from_browser = tool.get_all_cookie_from_browser(browser_type, cookie_path)
    if "www.instagram.com" in all_cookie_from_browser:
        for cookie_key in all_cookie_from_browser["www.instagram.com"]:
            COOKIE_INFO[cookie_key] = all_cookie_from_browser["www.instagram.com"][cookie_key]
    else:
        tool.print_msg("没有获取到登录信息，退出！")
        tool.process_exit()
    # 设置代理
    is_proxy = robot.get_config(config, "IS_PROXY", 2, 1)
    if is_proxy == 1 or is_proxy == 2:
        proxy_ip = robot.get_config(config, "PROXY_IP", "127.0.0.1", 0)
        proxy_port = robot.get_config(config, "PROXY_PORT", "8087", 0)
        # 使用代理的线程池
        net.set_proxy(proxy_ip, proxy_port)

    # 存档位置
    save_data_path = robot.get_config(config, "SAVE_DATA_PATH", "\\\\info/save.data", 3)
    # 读取存档文件
    account_list = robot.read_save_data(save_data_path, 0, [""])

    count = 0
    for account_name in sorted(account_list.keys()):
        account_index_response = get_account_index_page(account_name)
        if account_index_response.status == 404:
            log.error(account_name + " 账号不存在")
        elif account_index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
            log.error(account_name + " 首页访问失败，原因：%s" % robot.get_http_request_failed_reason(account_index_response.status))
            break

        if account_index_response.extra_info["account_id"] is None:
            log.error(account_name + " account id解析失败")
            tool.process_exit()

        if account_index_response.extra_info["is_follow"]:
            tool.print_msg("%s已经关注，跳过" % account_name)
        elif account_index_response.extra_info["is_private"] and not IS_FOLLOW_PRIVATE_ACCOUNT:
            tool.print_msg("%s是私密账号，跳过" % account_name)
        else:
            if follow_account(account_name, account_index_response.extra_info["account_id"]):
                count += 1
            time.sleep(0.1)

    tool.print_msg("关注完成，成功关注了%s个账号" % count)

if __name__ == "__main__":
    main()
