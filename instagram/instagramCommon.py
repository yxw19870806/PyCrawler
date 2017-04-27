# -*- coding:utf-8  -*-
"""
Instagram公共方法
https://www.instagram.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import os
import sys

USER_COUNT_PER_PAGE = 50
COOKIE_INFO = {"csrftoken": "", "sessionid": ""}


def set_csrf_token():
    global COOKIE_INFO
    home_page_url = "https://www.instagram.com/instagram"
    home_page_response = net.http_request(home_page_url)
    if home_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        set_cookie = net.get_cookies_from_response_header(home_page_response.headers)
        if "csrftoken" in set_cookie:
            COOKIE_INFO["csrftoken"] = set_cookie["csrftoken"]
            return True
    return False


# 从cookie中获取登录的sessionid
def set_session_id():
    global COOKIE_INFO
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
    if "www.instagram.com" in all_cookie_from_browser and "sessionid" in all_cookie_from_browser["www.instagram.com"]:
        COOKIE_INFO["sessionid"] = all_cookie_from_browser["www.instagram.com"]["sessionid"]


# 获取指定账号的所有粉丝列表（需要cookies）
# account_id -> 490060609
def get_follow_by_list(account_id):
    # 从cookies中获取session id的值
    set_session_id()
    # 从页面中获取csrf token的值
    if not COOKIE_INFO["csrftoken"]:
        set_csrf_token()

    cursor = None
    follow_by_list = []
    while True:
        query_page_url = "https://www.instagram.com/query/"
        # node支持的字段：id,is_verified,followed_by_viewer,requested_by_viewer,full_name,profile_pic_url,username
        if cursor is None:
            post_data = {"q": "ig_user(%s){followed_by.first(%s){nodes{username},page_info}}" % (account_id, USER_COUNT_PER_PAGE)}
        else:
            post_data = {"q": "ig_user(%s){followed_by.after(%s,%s){nodes{username},page_info}}" % (account_id, cursor, USER_COUNT_PER_PAGE)}
        header_list = {"Referer": "https://www.instagram.com/", "X-CSRFToken": COOKIE_INFO["csrftoken"]}
        follow_by_page_response = net.http_request(query_page_url, method="POST", post_data=post_data, header_list=header_list, cookies_list=COOKIE_INFO, json_decode=True)
        if follow_by_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            if robot.check_sub_key(("followed_by",), follow_by_page_response.json_data) and robot.check_sub_key(("page_info", "nodes"), follow_by_page_response.json_data["followed_by"]):
                for node in follow_by_page_response.json_data["followed_by"]["nodes"]:
                    if robot.check_sub_key(("username",), node):
                        follow_by_list.append(node["username"])
                if robot.check_sub_key(("end_cursor", "has_next_page"), follow_by_page_response.json_data["followed_by"]["page_info"]):
                    if follow_by_page_response.json_data["followed_by"]["page_info"]["has_next_page"]:
                        cursor = follow_by_page_response.json_data["followed_by"]["page_info"]["end_cursor"]
                        continue
        break
    return follow_by_list


# 获取指定账号的所有关注列表（需要cookies）
# account_id -> 490060609
def get_follow_list(account_id):
    # 从cookies中获取session id的值
    set_session_id()
    # 从页面中获取csrf token的值
    if not COOKIE_INFO["csrftoken"]:
        set_csrf_token()

    cursor = None
    follow_list = []
    while True:
        query_page_url = "https://www.instagram.com/query/"
        # node支持的字段：id,is_verified,followed_by_viewer,requested_by_viewer,full_name,profile_pic_url,username
        if cursor is None:
            post_data = {"q": "ig_user(%s){follows.first(%s){nodes{username},page_info}}" % (account_id, USER_COUNT_PER_PAGE)}
        else:
            post_data = {"q": "ig_user(%s){follows.after(%s,%s){nodes{username},page_info}}" % (account_id, cursor, USER_COUNT_PER_PAGE)}
        header_list = {"Referer": "https://www.instagram.com/", "X-CSRFToken": COOKIE_INFO["csrftoken"]}
        follow_page_response = net.http_request(query_page_url, method="POST", post_data=post_data, header_list=header_list, cookies_list=COOKIE_INFO, json_decode=True)
        if follow_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            if robot.check_sub_key(("follows",), follow_page_response.json_data) and robot.check_sub_key(("page_info", "nodes"), follow_page_response.json_data["follows"]):
                for node in follow_page_response.json_data["follows"]["nodes"]:
                    if robot.check_sub_key(("username",), node):
                        follow_list.append(node["username"])
                if robot.check_sub_key(("end_cursor", "has_next_page"), follow_page_response.json_data["follows"]["page_info"]):
                    if follow_page_response.json_data["follows"]["page_info"]["has_next_page"]:
                        cursor = follow_page_response.json_data["follows"]["page_info"]["end_cursor"]
                        continue
        break
    return follow_list
