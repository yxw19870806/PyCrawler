# -*- coding:UTF-8  -*-
"""
Twitter公共方法
https://www.instagram.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import re
from common import *


# 从cookie中获取登录的auth_token
def get_auth_token():
    all_cookie_from_browser = crawler.quickly_get_all_cookies_from_browser()
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
    follow_pagination_url = "https://twitter.com/%s/following/users" % account_name
    query_data = {"max_position": position_id}
    cookies_list = {"auth_token": auth_token}
    follow_pagination_response = net.http_request(follow_pagination_url, method="GET", fields=query_data, cookies_list=cookies_list, json_decode=True)
    if follow_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if crawler.check_sub_key(("min_position", "has_more_items", "items_html"), follow_pagination_response.json_data):
            return follow_pagination_response.json_data
    return None
