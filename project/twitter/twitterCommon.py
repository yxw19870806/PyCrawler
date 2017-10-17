# -*- coding:UTF-8  -*-
"""
Twitter公共方法
https://www.instagram.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import re


# 从cookie中获取登录的auth_token
def get_auth_token():
    config = robot.read_config(tool.PROJECT_CONFIG_PATH)
    # 操作系统&浏览器
    browser_type = robot.get_config(config, "BROWSER_TYPE", 2, 1)
    # cookie
    is_auto_get_cookie = robot.get_config(config, "IS_AUTO_GET_COOKIE", True, 4)
    if is_auto_get_cookie:
        cookie_path = browser.get_default_browser_cookie_path(browser_type)
    else:
        cookie_path = robot.get_config(config, "COOKIE_PATH", "", 0)
    all_cookie_from_browser = browser.get_all_cookie_from_browser(browser_type, cookie_path)
    if ".twitter.com" in all_cookie_from_browser and "auth_token" in all_cookie_from_browser[".twitter.com"]:
        return all_cookie_from_browser["www.instagram.com"]["sessionid"]
    return None


# 获取指定账号的全部关注列表（需要cookies）
def get_follow_list(account_name):
    position_id = "2000000000000000000"
    follow_list = []
    # 从cookies中获取auth_token
    auth_token = get_auth_token()
    if auth_token is None:
        return None
    while True:
        follow_pagination_data = get_one_page_follow(account_name, auth_token, position_id)
        if follow_pagination_data is not None:
            profile_list = re.findall('<div class="ProfileCard[^>]*data-screen-name="([^"]*)"[^>]*>', follow_pagination_data["items_html"])
            if len(profile_list) > 0:
                follow_list += profile_list
            if follow_pagination_data["has_more_items"]:
                position_id = follow_pagination_data["min_position"]
                continue
        break
    return follow_list


# 获取一页的关注列表
def get_one_page_follow(account_name, auth_token, position_id):
    follow_pagination_url = "https://twitter.com/%s/following/users?max_position=%s" % (account_name, position_id)
    cookies_list = {"auth_token": auth_token}
    follow_pagination_response = net.http_request(follow_pagination_url, cookies_list=cookies_list, json_decode=True)
    if follow_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if robot.check_sub_key(("min_position", "has_more_items", "items_html"), follow_pagination_response.json_data):
            return follow_pagination_response.json_data
    return None
